## Задание 1. Анализ и планирование

**Описание функциональности монолитного приложения**

Система обеспечивает управление отоплением умного дома. В текущей кодовой базе есть проблемы, не позволяющие в полной мере восстановить картину взаимодействия всех компонентов и функций системы, поэтому далее могут быть предположения.

Функциональность текущего приложения:
1. Контроль температуры (пользователь может получить данные температуры, вероятно, в отдельном приложении (сайте) или на самом устройстве)
2. Управление температурой (пользователь может управлять температурой, вероятно, в отдельном приложении или через механическое устройство/вентиль)
3. Администрирование сенсоров: регистрация и обслуживание (регистрация при включении, обслуживание мастером на дому)

**Анализ архитектуры монолитного приложения**

Архитектура системы представляет собой монолитное решение с единым компонентом (если под компонентом понимать единицу сборки), написанное на Go. Для хранения данных используется реляционная база данных PostgreSQL.  Взаимодействие с секретами приложения осуществляется через операционную систему, секреты базы данных заданы в docker-compose.yml.
Все коммуникации системы – синхронные. Сервер выступает активной стороной, опрашивая состояние устройств, своего рода long  polling'ом.
При публикации система недоступна, так как обновляется целиком

**Определение доменов и границ контекстов**

Текущее решение небольшое с ограниченными функциональными возможностями, для себя выделяю один *домен - *теплый дом**.

Контексты определены исходя из соотношения функционала системы и используемого языка (ubiquitous language)
* Контекст управления теплым домом (контроль температуры, управление температурой)
* Контекст поддержки теплого дома (регистрация и обслуживание устройств)

**Проблемы монолитного решения**

Текущее решение удовлетворяло требования бизнеса до момента масштабирования. Потенциальные проблемы, которые могут возникнуть при расширении системы:  

* Невозможность масштабирования отдельных функций системы под разную нагрузку

* Высокое количество лишних запросов от сервера и задержки (из-за синхронного взаимодействия и опроса устройств сервером). При росте количества устройств подход активного сервера (опрашивающего) становится неадекватным.

* Проблемы с работой нескольких разработчиков над общей кодовой базой

* Проблемы с несовместимостью наборов нефункциональных требований при росте функционала разных модулей/устройств, например, управление воротами требует повышенного контроля, управление видео требует широкого пропускного канала и, вероятно, учета data residency (разные требования к хранению и администрированию записей).

* Если изначальная версия приложения была on-premise (предположение), то этот факт может также служить ограничителем при необходимости быстро адаптировать приложение под новые реалии.

Визуализация контекста системы - диаграмма С4:
[Диаграмма монолитного решения](as-is.puml)

## Задание 2. Проектирование микросервисной архитектуры
При декомпозиции сервисов желательно сделать так, чтобы при изменении требований не пришлось менять проектировочное решение (добавлять или убавлять сервисы), а также использовать минимальное количество сервисов для достижения основных целей бизнеса. 
Основным доменом определю "Coziness" - Благополучение. Так как умный дом создается для обеспечения благополучия обиталей. 
Касаемо поддоменов и контекстов:
1. Поддомен "Администрирование". Основной функционал по регистрации, настройке устройств и сценариев. 
Контекст: менеджмент устройств

Описание сервисов и баз поддомена:
- Management Gateway
Сервис на go, принимающий запросы с UI пользователей. Создан для проксирования запросов в Device Management.
- Device Management. 
Сервис на python (Fast API). Создан для регистрации пользователей и устройств, создания записей о домах и комнатах, устройствах в них и задании автоматизированных сценариев, которые исполняются в сервисе Action Initiation. 
- Реляционная база данных PostgreSQL. Реляционная база данных выбрана для простоты работы и скорости интеграции. От системы менеджмента не требуется каких-то специфических особенностей в разрезе производительности, неструктирированности и т.п.


2. Поддомен "Жизнь устройств". Основной функционал работы с устройствами, изменение состояния, контроль состояния, исполнение сценариев.
Контексты: 
2.1 Исполнение сценариев
2.2 Потоковая обработка
2.3. Контроль состояния

Описание сервисов и баз поддомена:

- Сервис Action Initiation. Сервис на node, созданный для изменения состояния устройств и исполнения сценариев. Изначально была идея поделить Action Initiation на разные по приоритету сервисы. В одном из них исполнять срочные задачи, связанные с безопасностью и требующие мгновенного отклика, в другом исполнение несрочных задач (включит пылесос, включить чайник). 
- База данных для Action Initiation - Immutable Storage (EventStore). База создана для ведения непротиворечивого (за счет иммутабельности) лога активности устройств.

- Сервис Streaming Gateway. Go сервис, созданный для приема потоковых данных с устройств (audio/video).
- Сервис Minio - S3. Для хранения аудио, видео-файлов потоковой обработки

- Native Device Gateway. Gateway на Go для проксирования устройств нативных устройств умного дома. Проксирует данные в Device Metrics.
- Side Device Gateway. Gateway на Go для проксирования устройств партнеров. Внутри расположен маппер (кода под него не написано, но он подразумевается), который приводит формат данных к стандарту системы. Проксирует данные в Device Metrics.
- Сервис Device Metrics написанный на .NET. Сервис для сбора логов и метрик с устройств.
- Promotheus, Grafana, Loki. Стек для сбора метрик, логирования и визуализации. Получает данные из Device Metrics.

3. Поддомен "Коммуникация". Все что связано с оповещением и обратной связью клиентов системы умного дома.
3.1 Контекст "Оповещения"
3.2. Контекст "Техническая поддержка"

Описание сервисов и баз поддомена:

- Сервис Notification. Node сервис для рассылки оповещений и предупреждений клиентам системы.
- База данных Notification - Immutable Storage - EventStore. Для иммутабельного лога оповещений и предупреждений.
- Сервис Supporting. Node сервис для приема заявок на техническую поддержку с внешних систем. Может быть развит до полноценной системы обратной связи.
- База данных Supporting сервиса - NoSQL. Для сбора неструктурированных заявок на обработку обратной связи или тикетов.

Новая система учитывает необходимость асинхронного взаимодействия для повышения доступности и масштабируемости системы.

Интеграграция с legacy-системой реализована через go-bridge-for-legacy сервис (маппинг из старой модели в новую и обращение к роуту внутреннего сервиса администрирования). C учетом подключенных 100 домов, проблем с производительностью при взаимодействии bridge->management service (HTTP) быть не должно.

[Диаграмма контекста](schemas/to-be-context.puml)
[Диаграмма контейнеров](schemas/to-be-containers.puml)

## Задание 3. Разработка ER-диаграммы

Ниже представлена простая схема таблиц умного дома, системы администрирования, контекста "Менеджмент устройств"

Таблица users
| Column          | Type             | Notes          |
| :-------------- | :--------------- | :------------- |
| `id`            | `UUID` **PK**    | primary key    |
| `email`         | `VARCHAR`        | unique login   |
| `name`          | `VARCHAR`        | display name   |
| `registered_at` | `TIMESTAMP`      | creation date  |
| `phone`         | `VARCHAR` `NULL` | optional phone |

Таблица homes
| Column     | Type                     | Notes           |
| :--------- | :----------------------- | :-------------- |
| `id`       | `UUID` **PK**            |                 |
| `name`     | `VARCHAR`                | home/flat label |
| `address`  | `VARCHAR` `NULL`         | postal address  |
| `owner_id` | `UUID` **FK → users.id** | home owner      |

Таблица rooms
| Column    | Type                     | Notes                             |
| :-------- | :----------------------- | :-------------------------------- |
| `id`      | `UUID` **PK**            |                                   |
| `name`    | `VARCHAR`                | room label                        |
| `info`    | `VARCHAR` `NULL`         | description (e.g. “Kids bedroom”) |
| `home_id` | `UUID` **FK → homes.id** | parent home                       |

Таблица devices
| Column             | Type                            | Notes                        |
| :----------------- | :------------------------------ | :--------------------------- |
| `id`               | `UUID` **PK**                   |                              |
| `name`             | `VARCHAR`                       | logical name                 |
| `type`             | `ENUM(DeviceType)`              | `SENSOR`, `CAMERA`, `SWITCH` |
| `model`            | `VARCHAR`                       | device model                 |
| `firmware_version` | `VARCHAR`                       | firmware build               |
| `status`           | `VARCHAR`                       | arbitrary status             |
| `room_id`          | `UUID` **FK → rooms.id** `NULL` | installed room               |
| `home_id`          | `UUID` **FK → homes.id** `NULL` | direct link to home          |
| `activation_code`  | `VARCHAR` `UNIQUE` `NULL`       | pairing token                |
| `is_activated`     | `BOOLEAN` default `FALSE`       |                              |
| `activated_at`     | `TIMESTAMP` `NULL`              | activation time              |

Таблица automation_scenarios
| Column       | Type                     | Notes          |
| :----------- | :----------------------- | :------------- |
| `id`         | `UUID` **PK**            |                |
| `name`       | `VARCHAR`                | scenario title |
| `user_id`    | `UUID` **FK → users.id** |                |
| `enabled`    | `BOOLEAN` default `TRUE` |                |
| `created_at` | `TIMESTAMP`              |                |

Таблица automation_rules
| Column              | Type                                     | Notes                 |
| :------------------ | :--------------------------------------- | :-------------------- |
| `id`                | `UUID` **PK**                            |                       |
| `scenario_id`       | `UUID` **FK → automation\_scenarios.id** |                       |
| `trigger_type`      | `ENUM(TriggerType)`                      | `SENSOR`, `TIME`      |
| `trigger_condition` | `VARCHAR`                                | e.g. cron, JSON DSL   |
| `action_type`       | `ENUM(ActionType)`                       | `TURN_ON`, `TURN_OFF` |
| `action_target`     | `UUID` **FK → devices.id**               | target device         |

Таблица notification
| Column    | Type                      | Notes              |
| :-------- | :------------------------ | :----------------- |
| `id`      | `UUID` **PK**             |                    |
| `user_id` | `UUID` **FK → users.id**  |                    |
| `title`   | `VARCHAR`                 | notification title |
| `body`    | `TEXT`                    | full text          |
| `sent_at` | `TIMESTAMP`               |                    |
| `read`    | `BOOLEAN` default `FALSE` |                    |

[ERD-диаграмма](schemas/to-be-containers.puml)

## Задание 4. Создание и документирование API

Ссылка на полный [openapi.json](apps/device-management/openapi.json) сервиса администрирования

Ниже приведен пример сценария по созданию автоматизированной цепочки действий
examples:

Создание девайса:

POST http://localhost:8081/api/v2.0/sensors:
```
{
  "name": "Thermostat-YA",
  "type": "SENSOR",
  "model": "X-1000",
  "firmware_version": "1.0.2",
  "location":"kitchen",
  "unit":"celcius",
  "status": "active",
  "activation_code": "ABC123"
}
```
response: Created (200):
```
{
    "name": "Thermostat-YA",
    "type": "SENSOR",
    "model": "X-1000",
    "location": "kitchen",
    "unit": "celcius",
    "firmware_version": "1.0.2",
    "status": "active",
    "room_id": null,
    "home_id": null,
    "activation_code": "ABC123",
    "is_activated": false,
    "activated_at": null,
    "id": "938f1351-58d2-42b3-bf9a-e64cc728ef28"
}
```
-------------------------------------------------
POST http://localhost:8081/api/v2.0/sensors:
```
{
  "name": "Thermostat-YA",
  "type": "SENSOR",
  "model": "X-1000",
  "firmware_version": "1.0.2",
  "unit":"celcius",
  "status": "active",
  "activation_code": "ABC123"
}
```
response - Inprocessable Entity (422)
```
{
    "detail": [
        {
            "type": "missing",
            "loc": [
                "body",
                "location"
            ],
            "msg": "Field required",
            "input": {
                "name": "Thermostat-YA",
                "type": "SENSOR",
                "model": "X-1000",
                "firmware_version": "1.0.2",
                "unit": "celcius",
                "status": "active",
                "activation_code": "ABC123"
            }
        }
    ]
}
```
---------------------------------------------------
Создание пользователя:

POST http://localhost:8081/api/v2.0/users/register
```
{
  "email": "user1@example.com",
  "name": "User Name",
  "phone": "+123456789"
}
```
Created (201)
```
{
    "email": "user1@example.com",
    "name": "User Name",
    "phone": "+123456789",
    "id": "2badcd65-6a76-4702-9eea-1472ea6d0155",
    "registered_at": "2025-06-19T05:44:02.654659"
}
```
Repeat

Bad Request (400)
```
{
    "detail": "Email already registered"
}
```
-------------------------------------------------
Создание автоматизированного сценария:

POST http://localhost:8081/api/v2.0/automation-scenarios
```
{
  "name": "Night Lights Off",
  "user_id": "2badcd65-6a76-4702-9eea-1472ea6d0155",
  "rules": [
    {
      "trigger_type": "TIME",
      "trigger_condition": "22:00",
      "action_type": "TURN_OFF",
      "action_target": "938f1351-58d2-42b3-bf9a-e64cc728ef28"
    },
    {
      "trigger_type": "TIME",
      "trigger_condition": "08:00",
      "action_type": "TURN_ON",
      "action_target": "938f1351-58d2-42b3-bf9a-e64cc728ef28"
    }
  ]
}
```
Response: 201 Created
```
{
    "name": "Night Lights Off",
    "user_id": "fcc8d475-6f64-4591-9452-f04b41ffec36",
    "enabled": true,
    "id": "bcd41436-8230-4991-89b8-63bf489dd263",
    "created_at": "2025-06-19T05:17:01.698615",
    "rules": [
        {
            "scenario_id": "bcd41436-8230-4991-89b8-63bf489dd263",
            "trigger_type": "TIME",
            "trigger_condition": "22:00",
            "action_type": "TURN_OFF",
            "action_target": "064dd361-b947-4222-8771-7c95bd80af78",
            "id": "0cc3003a-09ab-4884-9dc9-b23725a24e5a"
        },
        {
            "scenario_id": "bcd41436-8230-4991-89b8-63bf489dd263",
            "trigger_type": "TIME",
            "trigger_condition": "08:00",
            "action_type": "TURN_ON",
            "action_target": "064dd361-b947-4222-8771-7c95bd80af78",
            "id": "1dd8f2c3-180b-447a-9779-826ec34e9efe"
        }
    ]
}
```
## Задание 5. Создание Dockerfile
Созданный монолит находится в директории legacy-monolith-temperature
Базовый url: http://localhost:8081/api/v1.0/

Проверить можно запустив docker-compose и обращаться по роутам:

POST: http://localhost:8081/api/v1.0/sensors
GET:  http://localhost:8081/api/v1.0/sensors

Раздел в docker-compose:
legacy-monolith:
    build: ./legacy-monolith-temperature/temperature-api/
    depends_on: 
      kafka:
        condition: service_healthy
      legacy-monolith-db:
        condition: service_started
    environment:
    - ASPNETCORE_URLS=http://0.0.0.0:8082
    - Kafka__BootstrapServers=kafka:9092
    ports:
      - "8082:8082"
  
  legacy-monolith-db:
    image: postgres:15-alpine
    volumes:
      - postgres_data_old:/var/lib/postgresql/data/
      - ./database-init/init-old-monolith-db.sql:/docker-entrypoint-initdb.d/init-old-monolith-db.sql:ro
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=smarthome
    ports:
      - 5430:5432


## Задание 6. Разработать микросервисы

см.docker-compose

Для запуска может потребоваться определенное время (несколько минут).
В решении создан каркас микросервисной системы с минимальным функционалом, обеспечивающим:
1. Администрацию пользователей, девайсов, автоматизированных сценариев, импровизированных нотификаций и изменений состояний устройств (node-action-initiation, node-notification)
2. Проксирование создания датчиков старого формата через go-bridge: http://localhost:8081/api/v1.0/sensors. 
Проверить можно создав датчик по api v1: POST http://localhost:8081/api/v1.0/sensors и запросив датчик по api v2: GET http://localhost:8081/api/v2.0/sensors
3. Сбор логирования, метрик
