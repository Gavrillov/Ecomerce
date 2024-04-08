import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from docx import Document
from flask import Flask, render_template, send_file, redirect, url_for, request, jsonify
import pyodbc

app = Flask(__name__)

# Функция подключения к БД
def connection():
    try:
        cnxn = pyodbc.connect("Driver={SQL Server};Server=KOMPUTER;Database=Volks;Trusted_Connection=yes;")
        return cnxn
    except pyodbc.Error as e:
        print(f"Ошибка подключения к БД: {str(e)}")
        return None

conn = connection()
cursor = conn.cursor()

# Функция авторизации
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            cursor.execute("SELECT id_role FROM Users WHERE login = ? AND password = ?", (username, password))
            row = cursor.fetchone()
            if row and row[0] == 4:  # Проверяем роль пользователя
                return redirect(url_for('managerdashboard'))
            else:
                return render_template('err404.html')
        except pyodbc.Error as e:
            return f"Ошибка при выполнении запроса: {str(e)}"

    return render_template('reg.html')

# Функция панели менеджера
@app.route('/managerdashboard', methods=['GET'])
def managerdashboard():
    try:
        cursor.execute("SELECT Orders.*, car.model, Users.name, Users.surname, Users.patronymic,Users.e_mail, payment_method.name_pay, Order_status.name_status "
                       "FROM Orders "
                       "JOIN car ON Orders.id_car = car.id_car "
                       "JOIN Users ON Orders.id_user = Users.id_user "
                       "JOIN payment_method ON Orders.id_payment_method = payment_method.id_payment_method "
                       "JOIN Order_status ON Orders.id_order_status = Order_status.id_order_status "
                       "WHERE car.model IS NOT NULL AND Users.name IS NOT NULL AND Users.surname IS NOT NULL AND Users.patronymic IS NOT NULL AND Users.e_mail IS NOT NULL AND "
                       "payment_method.name_pay IS NOT NULL AND Order_status.name_status IS NOT NULL AND Order_status.id_order_status = 4")
        orders = cursor.fetchall()
        return render_template('index.html', orders=orders)
    except pyodbc.Error as e:
        return f"Ошибка при выполнении запроса: {str(e)}"


# Функция обновления статуса заказа
@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    try:
        data = request.get_json()
        order_id = data['orderId']
        query = "UPDATE Orders SET id_order_status = 1 WHERE id_orders = ?"
        cursor.execute(query, order_id)
        data = request.get_json()

        from_email = 'volkswagen.2001@mail.ru'  # почта, котроя специально содана для приложения
        password = 'TjVjvvLZMC35nm0hphZ2'
        to_email = data['email'] # пароль от этой почты (лучше держать в отдельной файле config)
        msg = MIMEMultipart()
        message = (f'Ваш заказ с номером {order_id} - оплачен\n')

        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP('smtp.mail.ru: 587')
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        conn.commit()

        return jsonify({'message': 'Статус заказа успешно обновлен'})
    except (KeyError, pyodbc.Error) as e:
        return jsonify({'error': f'Ошибка при обновлении статуса заказа: {str(e)}'})

@app.route('/complete_order')
def complete_order():
    try:
        cursor.execute(
            "SELECT Orders.*, car.model, Users.name, Users.surname, Users.patronymic,Users.e_mail, payment_method.name_pay, Order_status.name_status "
            "FROM Orders "
            "JOIN car ON Orders.id_car = car.id_car "
            "JOIN Users ON Orders.id_user = Users.id_user "
            "JOIN payment_method ON Orders.id_payment_method = payment_method.id_payment_method "
            "JOIN Order_status ON Orders.id_order_status = Order_status.id_order_status "
            "WHERE car.model IS NOT NULL AND Users.name IS NOT NULL AND Users.surname IS NOT NULL AND Users.patronymic IS NOT NULL AND Users.e_mail IS NOT NULL AND "
            "payment_method.name_pay IS NOT NULL AND Order_status.name_status IS NOT NULL AND Order_status.id_order_status = 1")
        orders = cursor.fetchall()
        return render_template('complete_order.html', orders=orders)
    except pyodbc.Error as e:
        return f"Ошибка при выполнении запроса: {str(e)}"


@app.route('/memo')
def get_memo():
    docx_file = 'Files/памятка.docx'  # Замените на путь к вашему документу Word
    html_content = convert_docx_to_html(docx_file)
    return render_template('memo.html', content = html_content)




def convert_docx_to_html(docx_file):
    doc = Document(docx_file)
    html_content = ''
    for paragraph in doc.paragraphs:
        html_content += f'<p>{paragraph.text}</p>'
    return html_content
if __name__ == '__main__':
    app.run()
