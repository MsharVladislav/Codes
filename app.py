from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import threading
import time
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Необходим для работы flash-сообщений

# Создание базы данных и таблиц
def init_db():
    conn = sqlite3.connect('new_bakery.db')
    c = conn.cursor()
    
    # Создание таблицы пекарей
    c.execute('''CREATE TABLE IF NOT EXISTS bakers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  full_name TEXT NOT NULL)''')
    
    # Создание таблицы выпечки
    c.execute('''CREATE TABLE IF NOT EXISTS pastries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  price REAL NOT NULL)''')
    
    # Создание таблицы заказов
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_name TEXT NOT NULL,
                  pastry_id INTEGER,
                  baker_id INTEGER,
                  order_type TEXT NOT NULL,
                  delivery BOOLEAN NOT NULL,
                  order_date DATETIME NOT NULL,
                  FOREIGN KEY (pastry_id) REFERENCES pastries (id),
                  FOREIGN KEY (baker_id) REFERENCES bakers (id))''')
    
    # Создание таблицы клиентов
    c.execute('''CREATE TABLE IF NOT EXISTS clients
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name TEXT NOT NULL,
              phone TEXT NOT NULL,
              email TEXT NOT NULL)''')

    # Создание таблицы доставки
    c.execute('''CREATE TABLE IF NOT EXISTS deliveries
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              order_id INTEGER,
              client_id INTEGER,
              address TEXT NOT NULL,
              delivered BOOLEAN NOT NULL,
              delivery_date DATETIME NOT NULL,
              FOREIGN KEY (order_id) REFERENCES orders (id),
              FOREIGN KEY (client_id) REFERENCES clients (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS completed_orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_name TEXT NOT NULL,
                  pastry_id INTEGER,
                  baker_id INTEGER,
                  order_type TEXT NOT NULL,
                  delivery BOOLEAN NOT NULL,
                  order_date DATETIME NOT NULL,
                  completion_date DATETIME NOT NULL,
                  FOREIGN KEY (pastry_id) REFERENCES pastries (id),
                  FOREIGN KEY (baker_id) REFERENCES bakers (id))''')
    
    # Добавление тестовых данных для пекарей
    c.execute("SELECT COUNT(*) FROM bakers")
    if c.fetchone()[0] == 0:
        bakers = [
            ('Иванов Иван Иванович',),
            ('Петров Петр Петрович',),
            ('Сидорова Мария Александровна',),
            ('Козлов Андрей Викторович',)
        ]
        c.executemany("INSERT INTO bakers (full_name) VALUES (?)", bakers)

    # Добавление тестовых данных для выпечки
    c.execute("SELECT COUNT(*) FROM pastries")
    if c.fetchone()[0] == 0:
        pastries = [
            ('Круассан', 100),
            ('Багет', 80),
            ('Пирог с яблоками', 150),
            ('Эклер', 120),
            ('Наполеон', 200)
        ]
        c.executemany("INSERT INTO pastries (name, price) VALUES (?, ?)", pastries)
    
    # Добавление тестовых клиентов 
    c.execute("SELECT COUNT(*) FROM clients")
    if c.fetchone()[0] == 0:
        clients = [
            ('Смирнов Алексей Иванович', '+7(900)123-45-67', 'smirnov@mail.ru'),
            ('Морозова Елена Петровна', '+7(911)987-65-43', 'morozova@gmail.com'),
            ('Волков Дмитрий Сергеевич', '+7(922)555-44-33', 'volkov@mail.ru'),
            ('Зайцева Ольга Андреевна', '+7(933)111-22-33', 'zaitseva@mail.ru')
        ]
        c.executemany("INSERT INTO clients (full_name, phone, email) VALUES (?, ?, ?)", clients)

    # Добавление тестовых заказов
    c.execute("SELECT COUNT(*) FROM orders")
    if c.fetchone()[0] == 0:
        orders = [
            ('Смирнов А.И.', 1, 1, 'на месте', False, datetime.now()),
            ('Морозова Е.П.', 2, 2, 'с собой', True, datetime.now()),
            ('Волков Д.С.', 3, 3, 'доставка', True, datetime.now()),
            ('Зайцева О.А.', 1, 4, 'на месте', False, datetime.now())
        ]
        c.executemany("""INSERT INTO orders 
                        (client_name, pastry_id, baker_id, order_type, delivery, order_date) 
                        VALUES (?, ?, ?, ?, ?, ?)""", orders)

    # Добавление тестовых доставок
    c.execute("SELECT COUNT(*) FROM deliveries")
    if c.fetchone()[0] == 0:
        deliveries = [
            (2, 2, 'ул. Ленина, 15, кв. 45', True, datetime.now()),
            (3, 3, 'пр. Мира, 28, кв. 12', False, datetime.now()),
            (4, 4, 'ул. Гагарина, 7, кв. 89', True, datetime.now())
        ]
        c.executemany("""INSERT INTO deliveries
                        (order_id, client_id, address, delivered, delivery_date)
                        VALUES (?, ?, ?, ?, ?)""", deliveries)
        
    # Добавляем таблицу отзывов
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  author TEXT NOT NULL,
                  content TEXT NOT NULL,
                  rating INTEGER NOT NULL,
                  date DATETIME NOT NULL,
                  delete_key TEXT NOT NULL)''')
    
    # Добавляем тестовые отзывы
    c.execute("SELECT COUNT(*) FROM reviews")
    if c.fetchone()[0] == 0:
        test_reviews = [
            ('Анна Иванова', 'Прекрасная пекарня! Круассаны просто восхитительные!', 5, 
             datetime.now(), 'key1'),
            ('Михаил Петров', 'Очень вкусные багеты, но хотелось бы больше выбора.', 4, 
             datetime.now(), 'key2'),
            ('Елена Сидорова', 'Замечательное обслуживание и уютная атмосфера.', 5, 
             datetime.now(), 'key3')
        ]
        c.executemany("""INSERT INTO reviews (author, content, rating, date, delete_key)
                        VALUES (?, ?, ?, ?, ?)""", test_reviews)
        
    c.execute('''CREATE TABLE IF NOT EXISTS news
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  date DATETIME NOT NULL,
                  image_name TEXT)''')
    
    # Добавляем тестовые новости
    c.execute("SELECT COUNT(*) FROM news")
    if c.fetchone()[0] == 0:
        test_news = [
            ('Открытие летней веранды!', 
             'Рады сообщить, что с 1 июня начинает работу наша уютная летняя веранда. '
             'Теперь вы можете наслаждаться свежей выпечкой на свежем воздухе!',
             datetime.now(), 'terrace.jpg'),
            ('Новинка: безглютеновый хлеб', 
             'В нашем ассортименте появился безглютеновый хлеб. Теперь наша пекарня '
             'становится еще доступнее для людей с особыми диетическими потребностями.',
             datetime.now(), 'gluten_free.jpg'),
            ('Мастер-класс по выпечке круассанов', 
             'В эту субботу в 15:00 приглашаем всех на мастер-класс по выпечке '
             'настоящих французских круассанов. Количество мест ограничено!',
             datetime.now(), 'masterclass.jpg')
        ]
        c.executemany("INSERT INTO news (title, content, date, image_name) VALUES (?, ?, ?, ?)",
                     test_news)
        
    # Добавляем таблицу категорий выпечки
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL)''')
                  
    # Добавляем таблицу выпечки
    c.execute('''CREATE TABLE IF NOT EXISTS bakery_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  price REAL NOT NULL,
                  category_id INTEGER,
                  FOREIGN KEY (category_id) REFERENCES categories (id))''')
    
    # Добавляем тестовые категории и товары, если их еще нет
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        categories = [
            ('Хлеб',),
            ('Булочки',),
            ('Пироги',),
            ('Круассаны',),
            ('Печенье',),
            ('Торты',)
        ]
        c.executemany("INSERT INTO categories (name) VALUES (?)", categories)
        
        bakery_items = [
            # Хлеб
            ('Багет французский', 'Классический французский багет с хрустящей корочкой', 89.00, 1),
            ('Чиабатта', 'Итальянский белый хлеб с большими порами', 95.00, 1),
            ('Бородинский', 'Темный заварной хлеб с кориандром', 75.00, 1),
            ('Цельнозерновой', 'Полезный хлеб из цельнозерновой муки', 85.00, 1),
            
            # Булочки
            ('Синнабон', 'Булочка с корицей и сливочной глазурью', 129.00, 2),
            ('Улитка с маком', 'Сдобная булочка с маковой начинкой', 65.00, 2),
            ('Ватрушка с творогом', 'Классическая булочка с творожной начинкой', 75.00, 2),
            
            # Пироги
            ('Яблочный пирог', 'Традиционный пирог с яблоками и корицей', 299.00, 3),
            ('Пирог с вишней', 'Песочный пирог с вишневой начинкой', 329.00, 3),
            ('Киш лорен', 'Французский пирог с ветчиной и сыром', 389.00, 3),
            
            # Круассаны
            ('Классический круассан', 'Слоеный круассан из сливочного масла', 89.00, 4),
            ('Миндальный круассан', 'Круассан с миндальным кремом', 129.00, 4),
            ('Шоколадный круассан', 'Круассан с шоколадной начинкой', 119.00, 4),
            
            # Печенье
            ('Овсяное', 'Классическое овсяное печенье с изюмом', 45.00, 5),
            ('Шоколадное', 'Печенье с кусочками шоколада', 55.00, 5),
            ('Макарон', 'Французское миндальное печенье', 89.00, 5),
            
            # Торты
            ('Наполеон', 'Классический слоеный торт с заварным кремом', 899.00, 6),
            ('Медовик', 'Медовые коржи с нежным сметанным кремом', 799.00, 6),
            ('Чизкейк', 'Нью-Йоркский чизкейк', 899.00, 6)
        ]
        c.executemany("INSERT INTO bakery_items (name, description, price, category_id) VALUES (?, ?, ?, ?)", 
                     bakery_items)
    
    conn.commit()
    conn.close()

def move_order_to_completed():
    while True:
        try:
            conn = sqlite3.connect('new_bakery.db')
            c = conn.cursor()
            
            # Получаем самый старый незавершенный заказ
            c.execute("""SELECT * FROM orders ORDER BY order_date ASC LIMIT 1""")
            order = c.fetchone()
            
            if order:
                # Добавляем заказ в таблицу завершенных
                c.execute("""INSERT INTO completed_orders 
                           (client_name, pastry_id, baker_id, order_type, delivery, order_date, completion_date)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (order[1], order[2], order[3], order[4], order[5], order[6], datetime.now()))
                
                # Удаляем заказ из таблицы текущих заказов
                c.execute("DELETE FROM orders WHERE id = ?", (order[0],))
                
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Error in move_order_to_completed: {e}")
        
        time.sleep(60)  # Ждем 1 минуту

# Запускаем фоновый поток для перемещения заказов
background_thread = threading.Thread(target=move_order_to_completed, daemon=True)
background_thread.start()

# Инициализация базы данных
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/order', methods=['GET', 'POST'])
def order():
    conn = sqlite3.connect('new_bakery.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if request.method == 'POST':
        client_name = request.form['client_name']
        pastry_id = request.form['pastry']
        baker_id = request.form['baker']
        order_type = request.form['order_type']
        delivery = 1 if request.form.get('delivery') else 0
        
        c.execute("""INSERT INTO orders (client_name, pastry_id, baker_id, order_type, delivery, order_date)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                 (client_name, pastry_id, baker_id, order_type, delivery, datetime.now()))
        conn.commit()
        return redirect(url_for('order'))
    
    # Получение данных для форм
    c.execute("SELECT * FROM pastries")
    pastries = c.fetchall()
    
    c.execute("SELECT * FROM bakers")
    bakers = c.fetchall()
    
    # Получение списка текущих заказов
    c.execute("""SELECT orders.*, bakers.full_name as baker_name, pastries.name as pastry_name
                 FROM orders
                 JOIN bakers ON orders.baker_id = bakers.id
                 JOIN pastries ON orders.pastry_id = pastries.id
                 ORDER BY order_date DESC""")
    orders = c.fetchall()
    
    # Получение списка готовых заказов
    c.execute("""SELECT completed_orders.*, bakers.full_name as baker_name, pastries.name as pastry_name
                 FROM completed_orders
                 JOIN bakers ON completed_orders.baker_id = bakers.id
                 JOIN pastries ON completed_orders.pastry_id = pastries.id
                 ORDER BY completion_date DESC""")
    completed_orders = c.fetchall()
    
    conn.close()
    return render_template('order.html', 
                         pastries=pastries, 
                         bakers=bakers, 
                         orders=orders, 
                         completed_orders=completed_orders)

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    conn = sqlite3.connect('new_bakery.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if request.method == 'POST':
        author = request.form['author']
        content = request.form['content']
        rating = int(request.form['rating'])
        delete_key = request.form['delete_key']
        
        c.execute("""INSERT INTO reviews (author, content, rating, date, delete_key)
                     VALUES (?, ?, ?, ?, ?)""",
                 (author, content, rating, datetime.now(), delete_key))
        conn.commit()
        flash('Ваш отзыв успешно добавлен!')
        return redirect(url_for('reviews'))
    
    c.execute("SELECT * FROM reviews ORDER BY date DESC")
    reviews = c.fetchall()
    conn.close()
    
    return render_template('reviews.html', reviews=reviews)

@app.route('/delete_review', methods=['POST'])
def delete_review():
    review_id = request.form['review_id']
    delete_key = request.form['delete_key']
    
    conn = sqlite3.connect('new_bakery.db')
    c = conn.cursor()
    
    c.execute("SELECT delete_key FROM reviews WHERE id = ?", (review_id,))
    result = c.fetchone()
    
    if result and result[0] == delete_key:
        c.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
        flash('Отзыв успешно удален!')
    else:
        flash('Неверный ключ удаления!')
    
    conn.close()
    return redirect(url_for('reviews'))

@app.route('/news')
def news():
    conn = sqlite3.connect('new_bakery.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM news ORDER BY date DESC")
    news = c.fetchall()
    conn.close()
    
    return render_template('news.html', news=news, datetime=datetime)

@app.route('/models')
def models():
    return render_template('models.html')

@app.route('/menu')
def menu():
    conn = sqlite3.connect('new_bakery.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Получаем все категории и товары
    c.execute("""
        SELECT c.name as category_name, 
               b.name as item_name, 
               b.description, 
               b.price
        FROM categories c
        LEFT JOIN bakery_items b ON c.id = b.category_id
        ORDER BY c.id, b.name
    """)
    
    menu_items = c.fetchall()
    
    # Группируем товары по категориям
    menu_by_category = {}
    for item in menu_items:
        if item['category_name'] not in menu_by_category:
            menu_by_category[item['category_name']] = []
        menu_by_category[item['category_name']].append(item)
    
    conn.close()
    return render_template('menu.html', menu=menu_by_category)

def show_database_gui():
    root = tk.Tk()
    root.title("Bakery Database Viewer")
    root.geometry("800x600")

    # Создаем вкладки
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Список таблиц для отображения
    tables = [
        'bakers', 'pastries', 'orders', 'clients', 
        'deliveries', 'reviews', 'news', 'categories', 
        'bakery_items', 'completed_orders'
    ]

    # Функция для создания вкладки с данными таблицы
    def create_table_tab(table_name):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=table_name)

        # Создаем TreeView
        tree = ttk.Treeview(frame)
        tree.pack(fill=tk.BOTH, expand=True)

        # Подключаемся к базе данных
        conn = sqlite3.connect('new_bakery.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получаем данные
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Настройка столбцов
        tree['columns'] = columns
        tree.heading('#0', text='')
        tree.column('#0', width=0, stretch=tk.NO)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER)

        # Получаем данные таблицы
        cursor.execute(f"SELECT * FROM {table_name}")
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=tuple(row))

        conn.close()

    # Создаем вкладки для каждой таблицы
    for table in tables:
        create_table_tab(table)

    root.mainloop()

if __name__ == '__main__':
    # Запускаем GUI базы данных в отдельном потоке
    db_thread = threading.Thread(target=show_database_gui)
    db_thread.start()

    app.run(debug=True)