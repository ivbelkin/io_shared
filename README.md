# io_shared

Пакет предназначен для взаимодействия между разными интерпретаторами python>=2.7 на одной машине. Возможна также передача данных в другие процессы при соблюдении соглашений об именах. Основа реализации - файл в разделяемой памяти, отображенный в память (memory mapped file in shared memory) защищенный семафорами (semaphore).

## Высокоуровневый интерфейс

Типичным сценарием использования разделяемой памяти является следующий:
1. Есть два процесса - A и B, запущенные на одной машине
2. Процесс А имеет данные, которые передает процессу B
3. Процесс B обрабатывает данные и передает результат процессу A
4. Переход к п.2

В данном и похожем сценариях возможно использование сети или дисковых фаилов для организации взаимодействия. Но так как процессы предполагаются быть запущенными на одной машине, то возможно использование примитивов IPC, одним из которых выступает разделяемая память (Shared Memory), обеспечивающая высокую скорость передачи данных. Вторым примитивом, необходимым для упорядочивания доступа и защиты памяти от одновременного чтения/записи, является семафор (Semaphore).

Для максимального уменьшения пользовательского кода и поддержки этого сценария используется класс SharedAssign, имитирующий операцию присваивания между процессами.

### Пример взаимодействия с упорядочиванием чтения-записи

Рассмотрим задачу: необходимо осуществить обработку данных, поступающих из сети в виде ROS сообщений, с помощью нейросетевой модели.

Эта задача вписывается в рассмотренный ранее сценарий. Пусть в качестве процесса A выступает ROS узел на python2 и своим окружением, а в качестве процесса B - процесс python3 c нейросетевой моделью сегментации лидарных облаков. Путем подмены источника данных с диска на область разделяемой памяти можно осуществить обработку данных процессом B несмотря на невозможность прямого обращения к модели из python2, а также возможным сложностям при попытках установки зависимостей модели в ROS окружение.

**ros_node**

```python
cloud_share = NumpyShare('/cloud_share', '5M', 'put')
label_share = NumpyShare('/label_share', '5M', 'get')

# callback
cloud = msg_to_cloud(msg_cloud)
cloud_share.put(cloud)  # данные кладутся в общую память, устанавливается флаг
label = label_share.get()  # ожидание установки флага, получение данных
msg_label = label_to_msg(label)
pub.publish(msg_label)
```


**segmentator**

```python
cloud_share = NumpyShare('/cloud_share', '5M', 'get')
label_share = NumpyShare('/label_share', '5M', 'put')


# вместо загрузки данных с диска
cloud = cloud_share.get()  # ожидание установки флага, получение данных
# label = model(cloud)
label_share.put(label)  # данные кладутся в общую память, устанавливается флаг
```

## Низкоуровневый интерфейс

Представлен тремя классами: `UnsafeSharedMMap`, `SharedMMap`, `RWSharedMMap`

### Описание классов

`UnsafeSharedMMap` - Объединяет операции создания/открытия блока разделяемой памяти и отображения ее в адресное пространство текущего процесса. Операции чтения/записи не блокируют память для других процессов, что может привести к нарушению целостности данных. Использовать с осторожностью или для реализации своей логики защиты целостности. Можно работать как с изменяемой строкой или файлом (предоставляет интерфейс аналогичный [mmap.mmap](https://docs.python.org/2/library/mmap.html), так как унаследован от него)

`SharedMMap` - то же, что и `UnsafeSharedMMap`, но операции чтения/записи защищены с помощью одного семафора. Блокировка накладывается на весь блок памяти в менеджере контекста (`with SharedMMap.lock():`). То есть ВСЕ операции И чтения И записи ВСЕХ процессов в ЛЮБУЮ область памяти не пересекаются во времени. Унаследован от `UnsafeSharedMMap`.

`RWSharedMMap` - то же, что и `UnsafeSharedMMap`, но операции чтения/записи защищены с помощью двух семафоров. То есть ВСЕ операции записи не пересекаются во времени между собой и ВСЕМИ операциями чтения в ЛЮБУЮ область памяти (`with RWSharedMMap.lock_write():`). Операции чтения из ЛЮБОЙ области памяти МОГУТ пересекаться между собой (`with RWSharedMMap.lock_read():`), так как это безопасно. Унаследован от `UnsafeSharedMMap`.

### Базовый пример

```python
import io_shared
from io_shared import UnsafeSharedMMap, SharedMMap, FastSharedMMap

# --- UnsafeSharedMMap
data = b'Hello, World!!!'
shm = UnsafeSharedMMap('/my_share', 15)
shm.write(data)
shm.seek(0)
print(shm.readline())  # 'Hello, World!!!\n'
shm.close()

# --- SharedMMap
data = b'Hello, World!!!'
shm = SharedMMap('/my_share', 15)
try:
    shm.write(data)
except io_shared.WriteAccessError as e:
    print('Oops')
with shm.lock():
    shm.write(data)

shm.seek(0)  # безопасно, так как у каждого процесса свой указатель позиции

try:
    print(shm.readline())
except io_shared.ReadAccessError as e:
    print('Oops')
with shm.lock():
    print(shm.readline())  # 'Hello, World!!!\n'

# --- RWSharedMMap
data = b'Hello, World!!!'
shm = RWSharedMMap('/my_share', 15)
with shm.lock_write():
    shm.write(data)

shm.seek(0)

with shm.lock_read():
    print(shm.readline())  # 'Hello, World!!!\n'
```

### Пример сериализации/десериализации numpy.ndarray

```python
import numpy as np
from io_shared import RWSharedMMap

arr = np.array([1, 2, 3], dtype=np.float32)

shm = RWSharedMMap('/my_share', '1M')

shm.seek(0)
with shm.lock_write():
    np.save(shm, arr)
# для сравнения, сохранение в обычный файл выглядит так
#  np.save('arr.np', arr)
# или так
#  with open('arr.np', 'wb') as f:
#      np.save(f, arr)

shm.seek(0)
with shm.lock_read():
    arr2 = np.load(shm)
# для сравнения, чтение из обычного файла выглядит так
#  arr2 = np.load('arr.np')
# или так
#  with open('arr.np', 'rb') as f:
#      arr2 = np.load(f)
```
