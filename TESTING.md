Тестирование
===

В пакет Webdavclient включены следующие компоненты: 

- `webdav API`
- `resource API`
- `wdc`

Каждый из компонентов имеет свою <span style="text-decoration: underline">тестовую базу</span>.

### webdav API ###

Компонент webdav API содержит следующие <span style="text-decoration: underline">тестовые наборы</span>:

- настройка подключения
- аутентификация
- методы
- интеграционные тесты

#### Настройка подключения ####

Для инициализации клиента используется словарь (настройки подключения), содержащий набор опций подключения к webdav-серверу.

Настройки подключения имеют обязательные и не обязательные опции. К обязательным опциям относятся `webdav_hostname`, `webdav_login` и `webdav_password`.

Заполнение полей может быть валидным или не валидным.
Для проверки используются метод `valid?`.

```python
import webdav.client as wc
options = {
    'webdav_hostname': "https://webdav.server.ru",
    'webdav_login': "login",
    'webdav_password': "password"
}
client = wc.Client(options)
client.valid?
```

*Тестовый сценарий 1*

    Идентификатор: 1.1.1
    Название: Обязательные опции подключения
    Описание: В случае присутствия каждой из обязательных опций, 
              настройки подключения клиента будут валидными.

<span style="color: red">Красный случай</span>
```python
assert_that(client, is_(not_valid())
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(client, is_(valid())
```


*Тестовый сценарий 2*

    Идентификатор: 1.1.2
    Название: Валидность обязательных опций подключения
    Описание: В случае валидности обязательных опций, 
              настройки подключения клиента будут валидными.

<span style="color: red">Красный случай</span>
```python
#without webdav_hostname
#without webdav_login
#without webdav_password
#with proxy_login or proxy_password, but without proxy_hostname
#with proxy_password and proxy_hostname, but without proxy_login
assert_that(client, is_(not_valid())
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(client, is_(valid())
```


*Тестовый сценарий 3*

    Идентификатор: 1.1.3
    Название: Валидность сертификата
    Описание: При указании валидного файла и ключа сертификата, 
              настройки подключения клиента будут валидными.

<span style="color: red">Красный случай</span>
```python
#with key_path, but without cert_path
#key_path or cert_path not exists
assert_that(calling(client.is_valid), raises(CertificateNotValid))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.is_valid), is_not(raises(CertificateNotValid))
```

#### Аутентификация ####

При подключении к webdav-серверу, необходимо пройти у него basic-аутентификацию, для этого используются опции `webdav_login` и `webdav_password`. При наличии proxy-сервера, может потребоваться так же пройти аутентификацию и у proxy-сервера. Для proxy-сервера поддерживаются следующие виды аутентификации:

- `basic`
- `digest`
- `ntlm`
- `negotiate`


*Тестовый сценарий 1*

    Идентификатор: 1.2.1
    Название: Аутентификация с webdav-сервером
    Описание: При правильной аутентификации клиент подключается к webdav-серверу. 
    
<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.check), is_(not_suceess())
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.check), is_(suceess())
```


*Тестовый сценарий 2*

    Идентификатор: 1.2.2
    Название: Аутентификация с proxy-сервером
    Описание: При правильной аутентификации клиент подключается к webdav-серверу. 
    
<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.check), is_(not_suceess())
```

<span style="color: green">Зеленый случай</span>
```python
#basic
#digest
#ntlm
#negotiate
assert_that(calling(client.check), is_(suceess())
```

#### Методы ####

webdav API реализует следущие методы: `check`, `free`, `info`, `list`, `mkdir`, `clean`, `copy`, `move`, `download`, `upload`, `publish` и `unpublish`.


*Тестовый сценарий 1*

    Идентификатор: 1.3.1
    Название: Проверка существования ресурса
    Описание: В случае существования ресурса, результат выполнения метода check 
              будет успешным. 
              
<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.check).with_args(remote_path), is_(not_suceess())
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.check).with_args(remote_path), is_(suceess())
```


*Тестовый сценарий 2*

    Идентификатор: 1.3.2
    Название: Проверка свободного места
    Описание: В случае если webdav-сервер поддерживает метод free, метод возвращает 
              размер свободного места.
              
<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.free), raises(MethodNotSupported))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.free), greater_than(0))
```


*Тестовый сценарий 3*

    Идентификатор: 1.3.3
    Название: Получение информации о ресурсе
    Описание: В случае если webdav-сервер поддерживает метод info,
              метод возвращает информацию следующего типа: 
              - дата создания;
              - дата модификации; 
              - размер;
              - имя.


<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.info).with_args(remote_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
info = client(remote_path)
assert_that(info, has_key("data1"))
assert_that(info, has_key("data2"))
assert_that(info, has_key("size"))
assert_that(info, has_key("name"))
```


*Тестовый сценарий 4*

    Идентификатор: 1.3.4
    Название: Получение списка ресурсов
    Описание: В случае, если указанный ресурс существует и является директорией, то метод list 
              возвращает список ресурсов, находящихся в данном ресурсе.


<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.info).with_args(remote_file), raises(RemoteResourceNotFound))
assert_that(calling(client.list).with_args(remote_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
files = client.list(remote_path)
assert_that(files, not_none()))
```


*Тестовый сценарий 5*

    Идентификатор: 1.3.5
    Название: Создание директории
    Описание: В случае, если все директории из путевого разбиения для 
              указанного ресурса существуют, то данный ресурс будет создан.


<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.info).with_args(remote_path), raises(RemoteParentNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
client.mkdir(remote_path)
assert_that(calling(client.check).with_args(remote_path), is_(success()))
```


*Тестовый сценарий 6*

    Идентификатор: 1.3.6
    Название: Удаление ресурса
    Описание: В случае, если указанный ресурс существует и не является корнем, то 
              метод clean удалит данный ресурс.


<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.clean).with_args(remote_path), raises(RemoteResourceNotFound))
assert_that(calling(client.clean).with_args(root), raises(InvalidOption))
```

<span style="color: green">Зеленый случай</span>
```python
client.clean(remote_path)
assert_that(calling(client.check).with_args(remote_path), is_(not_success()))
```


*Тестовый сценарий 7*

    Идентификатор: 1.3.7
    Название: Копирование ресурса
    Описание: В случае, если указанный ресурс существует и не является корнем, то 
              метод copy копирует данный ресурс.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.copy).with_args(from_path=remote_path, to_path=new_path), raises(RemoteResourceNotFound))
assert_that(calling(client.copy).with_args(from_path=root, to_path=new_path), raises(InvalidOption))
assert_that(calling(client.copy).with_args(from_path=remote_path, to_path=root), raises(InvalidOption))
assert_that(calling(client.copy).with_args(from_path=remote_path, to_path=remote_path), is_not(raises(WebDavException)))
```

<span style="color: green">Зеленый случай</span>
```python
client.copy(from_path=remote_path, to_path=new_path)
assert_that(calling(client.check).with_args(new_path), is_(success()))
```


*Тестовый сценарий 8*

    Идентификатор: 1.3.8
    Название: Перемещение ресурса
    Описание: В случае, если указанный ресурс существует и не является корнем, то 
              метод move переместит данный ресурс.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.move).with_args(from_path=old_path, to_path=new_path), raises(RemoteResourceNotFound))
assert_that(calling(client.move).with_args(from_path=root, to_path=new_path), raises(InvalidOption))
assert_that(calling(client.move).with_args(from_path=old_path, to_path=root), raises(InvalidOption))
assert_that(calling(client.move).with_args(from_path=old_path, to_path=remote_path), is_not(raises(WebDavException)))
```

<span style="color: green">Зеленый случай</span>
```python
client.move(from_path=old_path, to_path=new_path)
assert_that(calling(client.check).with_args(old_path), is_(not_success()))
assert_that(calling(client.check).with_args(new_path), is_(success()))
```


*Тестовый сценарий 9*

    Идентификатор: 1.3.9
    Название: Загрузка ресурса
    Описание: В случае, если указанный ресурс существует,
              то метод download загрузит данный ресурс.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.download).with_args(remote_path=remote_path, local_path=local_path), raises(LocalResourceNotFound))
assert_that(calling(client.download).with_args(remote_path=remote_path, local_path=local_path), raises(RemoteResourceNotFound))
assert_that(calling(client.download).with_args(remote_path=remote_file, local_path=local_directory), raises(InvalidOption))
assert_that(calling(client.download).with_args(remote_path=remote_directory, local_path=local_file), raises(InvalidOption))
```

<span style="color: green">Зеленый случай</span>
```python
client.download(remote_path=remote_path, local_path=local_path)
assert_that(local_path, is_(exist()))
```


*Тестовый сценарий 10*

    Идентификатор: 1.3.10
    Название: Выгрузка ресурса
    Описание: В случае, если родительская директория указанный ресурса       
              существует, то метод upload выгрузит файл или директорию в 
              ресурс.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.upload).with_args(remote_path=remote_path, local_path=local_path), raises(RemoteParentNotFound))
assert_that(calling(client.upload).with_args(remote_path=remote_file, local_path=local_directory), raises(InvalidOption))
assert_that(calling(client.upload).with_args(remote_path=remote_directory, local_path=local_file), raises(InvalidOption))
```

<span style="color: green">Зеленый случай</span>
```python
client.upload(remote_path=remote_path, to_path=local_path)
assert_that(calling(client.check).with_args(remote_path), is_(success()))
```


*Тестовый сценарий 11*

    Идентификатор: 1.3.11
    Название: Публикация ресурса
    Описание: В случае, если указанный ресурс существует, то метод publish
              возвращает публичную ссылку на ресурс.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.publish).with_args(remote_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.publish).with_args(remote_path), is_not(raises(RemoteResourceNotFound))
link = client.publish(remote_path)
assert_that(link, starts_with("http")
```


*Тестовый сценарий 12*

    Идентификатор: 1.3.12
    Название: Отмена публикации ресурса
    Описание: В случае, если указанный ресурс существует, 
              то метод unpublish отменяет публикацию ресурса.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.unpublish).with_args(remote_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.unpublish).with_args(remote_path), is_not(raises(RemoteResourceNotFound))
```

### resource API ###

Компонент resource API состоит из следующих <span style="text-decoration: underline">тестовых наборов</span> методы:

- получение ресурса
- методы

#### Получение ресурса ####

Для получение ресурса, используется метод `resource`.


*Тестовый сценарий 1*

    Идентификатор: 2.1.1
    Название: Получение ресурса
    Описание: В случае, если указанный ресурс является директорией и существует, 
              то метод resource возвращает ресурс.
              В случае, если указанный ресурс является файлом, 
              то метод resource возвращает ресурс.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.resource).with_args(remote_directory), raises(RemoteResourceNotFound))
assert_that(calling(client.resource).with_args(remote_file), is_not(raises(RemoteResourceNotFound)))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.check).with_args(remote_path), is_(success())
res = client.resource(remote_path)
assert_that(res.check())
```

#### Методы ####

resource API реализует следущие методы: `check`, `clean`, `is_directory`, `rename`, `move`, `copy`, `info`, `read_from`, `read`, `read_async`, `write_to`, `write`, `write_async`, `publish` и `unpublish`.


*Тестовый сценарий 1*

    Идентификатор: 2.2.1
    Название: Проверка существования ресурса
    Описание: В случае, если указанный ресурс существует, 
              то результат метода check будет успешным.

<span style="color: red">Красный случай</span>
```python
assert_that(calling(client.resource).with_args(remote_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.check).with_args(remote_path), is_(success())
res = client.resource(remote_path)
assert_that(res.check())
```


*Тестовый сценарий 2*

    Идентификатор: 2.2.2
    Название: Удаление ресурса
    Описание: В случае, если указанный ресурс существует, 
              то метод clean удалит данный ресурс.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path) 
assert_that(calling(res.clean), is_not(raises(RemoteResourceNotFound)))
```

<span style="color: green">Зеленый случай</span>
```python
assert_that(calling(client.check).with_args(remote_path), is_(success())
res = client.resource(remote_path)
assert_that(res.check())
```


*Тестовый сценарий 3*

    Идентификатор: 2.2.3
    Название: Проверка является ли ресурс директорией
    Описание: В случае, если указанный ресурс является директорией, 
              то результат метода is_directory будет успешным.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_file) 
assert_that(calling(res.is_directory), is_(not_success()))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_directory) 
assert_that(calling(res.is_directory), is_(success()))
```


*Тестовый сценарий 4*

    Идентификатор: 2.2.4
    Название: Переименование ресурса
    Описание: В случае, если указанный ресурс существует, 
              то метод rename переименует данный ресурс.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path) 
assert_that(calling(res.rename).with_args(new_name), raises(RemoteResourceNotFound))
assert_that(calling(res.rename).with_args(new_name), raises(RemoteResourceAlreadyExists))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(old_path) 
res.rename(new_name)
new_path = res.urn
assert_that(calling(client.check).with_args(old_path), is_(not_success()))
assert_that(calling(client.check).with_args(new_path), is_(success()))
```


*Тестовый сценарий 5*

    Идентификатор: 2.2.5
    Название: Перемещение ресурса
    Описание: В случае, если указанный ресурс существует, 
              то метод move переместит данный ресурс.

<span style="color: red">Красный случай</span>
```python
res = client.resource(old_path)
assert_that(calling(res.move).with_args(new_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(old_path) 
res.move(new_path)
assert_that(calling(client.check).with_args(old_path), is_(not_success()))
assert_that(calling(client.check).with_args(new_path), is_(success()))
```


*Тестовый сценарий 6*

    Идентификатор: 2.2.6
    Название: Копирование ресурса
    Описание: В случае, если указанный ресурс существует, 
              то метод copy скопирует данный ресурс.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path) 
assert_that(calling(res.copy).with_args(to_path), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_path) 
res.copy(new_path)
assert_that(calling(client.check).with_args(remote_path), is_(success()))
assert_that(calling(client.check).with_args(new_path), is_(success()))
```


*Тестовый сценарий 7*

    Идентификатор: 2.2.7
    Название: Получение информации о ресурсе
    Описание: В случае, если указанный ресурс существует, 
              то метод info возвращает информацию следующего типа:
              - дата создания;
              - дата модификации; 
              - размер;
              - имя.


<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path)
assert_that(calling(res.info), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_path)
info = res.info()
assert_that(info, has_key("data1"))
assert_that(info, has_key("data2"))
assert_that(info, has_key("size"))
assert_that(info, has_key("name"))
```


*Тестовый сценарий 8*

    Идентификатор: 2.2.8
    Название: Считывание данных с буфера в ресурс
    Описание: В случае, если указанный ресурс не является директорией,
              то метод read_from считывет содержимое буфера и записывает в ресурс.

<span style="color: red">Красный случай</span>
```python
res1 = client.resource(remote_file) 
assert_that(buff, is_(empty))
assert_that(calling(res1.read_from).with_args(buff), raises(BufferIsEmpty))

res2 = client.resource(remote_directory) 
assert_that(calling(res2.read_from).with_args(buff), raises(ResourceIsNotDirectory))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_path)
res.read_from(buff)
res_size = res.info("size")
assert_that(buff.size(), equal_to(res_size))
```


*Тестовый сценарий 9*

    Идентификатор: 2.2.9
    Название: Запись данных в буфер
    Описание: В случае, если указанный ресурс не является директорией,
              то метод write_to записывает содержимое ресурса в буфер.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path) 
assert_that(calling(res.write_to).with_args(buff), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_path)
res.write_to(buff)
res_size = res.info("size")
assert_that(buff.size(), equal_to(res_size))
```


*Тестовый сценарий 10*

    Идентификатор: 2.2.10
    Название: Публикация ресурса
    Описание: В случае, если указанный ресурс существует, то метод publish
              возвращает публичную ссылку на ресурс.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path)
assert_that(calling(res.publish), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_path)
assert_that(calling(res.publish), is_not(raises(RemoteResourceNotFound))
link = res.publish()
assert_that(link, starts_with("http")
```


*Тестовый сценарий 11*

    Идентификатор: 2.2.11
    Название: Отмена публикации ресурса
    Описание: В случае, если указанный ресурс существует, 
              то метод unpublish отменяет публикацию ресурса.

<span style="color: red">Красный случай</span>
```python
res = client.resource(remote_path)
assert_that(calling(res.unpublish), raises(RemoteResourceNotFound))
```

<span style="color: green">Зеленый случай</span>
```python
res = client.resource(remote_path)
assert_that(calling(res.unpublish).with_args(remote_path), is_not(raises(RemoteResourceNotFound))
```
