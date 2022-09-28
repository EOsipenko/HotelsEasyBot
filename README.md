![logo](images\logo.jpg)
# **HotelsEasyBot**
Телеграм-бот "HotelsEasy" для удобного поиска отелей.

## **Для пользователей**
При команде `/start` или сообщении "Привет" бот приветствует пользователя и предлагает начать работу или воспользоваться командой `/help`.

Также пользователь может обратиться к меню и выбрать команду:

![screenshot_1](images\screenshot_1.jpg)

При вводе команды `/help` пользователю выводится список кликабельных команд (те же, что и в меню).

### **Список возможностей бота**:
- **Lowprice** (`/lowprice`) - поиск топа самых дешёвых отелей в городе. Единственный критерий отбора - цена.
- **Highprice** (`/highprice`) - поиск топа самых дорогих отелей в городе. Единственный критерий отбора (как и у **Lowprice**) - цена.
- **Bestdeal** (`/bestdeal`) - поиск самых дешёвых отелей, которые находятся ближе всего к центру города. Пользователь указывает максимальную стоимость номера отеля (за сутки) и максимальную удалённость его от центра.
- **History** (`/history`) - выводится история поиска отелей (последние 5 поисковых запросов).

>*Уточнение*: все цены указываются в долларах США, расстояния - в километрах.

### **Процесс работы бота**:
При первых трёх командах пользователю задаются уточняющие вопросы: 
- город пребывания;
- даты;
- количество отелей, которые нужно отобразить;
- необходимости вывода фотографий и их количестве;
- вывод результатов поиска.

При команде **Bestdeal** также спрашивается про максимальную стоимость номера отеля и удалённость его от центра.

Итоговая информация, которая выводится пользователю по каждому отелю, выглядит так:
- Название отеля
- Цена
- Цена за все дни пребывания
- Удалённость от центра
- Ссылка на отель (на странице сайта hotels.com)
- Фотографии

![screenshot_2](images/screenshot_2.jpg)

Результаты поиска сохраняются и впоследствии с помощью команды **History** (`/history`) пользователь может узнать историю своего поиска.

## **Для разработчиков**
- Для работы проекта используется открытый API Hotels.com, который расположен на
сайте [rapidapi.com](https://rapidapi.com/ru/hub) (документация по работе с API [здесь](https://rapidapi.com/ru/apidojo/api/hotels4/)).
- Запуск бота производится из главного файла `main.py`.
- Конфиденциальные данные (токен бота, токен RapidAPI) находятся в среде окружения (.env).
- Сортировка отелей, их сохранение и вывод пользователю при командах `/lowprice` и `/highprice` определяется самим сервисом rapidAPI; сортировка при команде `/bestdeal` - сначала по расстоянию, затем по цене.
- Данные поисковых запросов сохраняются в файле проекта `search_requests.json`. Для ID каждого пользователя данные сохраняются по дате и времени поискового запроса.
- Благодаря сохранению результатов поисковых запросов в файл проекта, эти данные не пропадают при перезапуске бота (преднамеренном или вызванном непредвиденными ситуациями).

Библиотеки, используемые в проекте:
- pyTelegramBotAPI 4.7.0
- dotenv 0.21.0
- requests
- json
- re
- datetime
- operator
- typing


## *Автор проекта*
*Эдуард Осипенко, Калининград*

##### **лого телеграм-бота создано при помощи сервиса [Logaster](https://www.logaster.ru/)*
