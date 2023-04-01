import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
import glob
import matplotlib as plt
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from email.mime.application import MIMEApplication
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

app = Flask(__name__)
app.secret_key = 'mysecretkey'

############################## HOME PAGE ################################


@app.route('/', methods=['GET'])
def home():
    if 'admin' in session:
        return render_template('home.html', button='logout')
    else:
        return render_template('home.html', button='admin_login')


############################## STUDENT FORM PAGE ################################
@app.route('/studentform', methods=['GET', 'POST'])
def studentform():
    if request.method == 'POST':
        name = request.form['name']
        moodle_id = request.form['moodle_id']
        email = request.form['email']
        parent_email = request.form['parent_email']
        contact_number = request.form['contact_number']

        # Insert data into database
        conn = pymysql.connect(host='localhost', user='root', password='',
                               database='ai_based_student_monitoring', port=3307)
        cur = conn.cursor()
        cur.execute('INSERT INTO student_info (name, moodle_id, email, parent_email, contact_number) VALUES (%s, %s, %s, %s, %s)',
                    (name, moodle_id, email, parent_email, contact_number))
        conn.commit()
        cur.close()
        conn.close()

        # Append data to CSV file
        data = {'Name': name, 'Moodle ID': moodle_id, 'Email ID': email,
                "Parent's Email": parent_email, 'Contact Number': contact_number}
        file_path = 'studentdetails.csv'
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='') as csv_file:
            fieldnames = ['Name', 'Moodle ID', 'Email ID',
                          "Parent's Email", 'Contact Number']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        message = 'Form submitted successfully!'
        return render_template('studentform.html', message=message)
    else:
        return render_template('studentform.html')


############################## ADMIN LOGIN PAGE ################################
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # check if the username and password are correct
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin_login.html')


############################## STUDENT INFO PAGE ################################
@app.route('/admin_dashboard')
def admin_dashboard():
    # check if admin is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = pymysql.connect(host='localhost', user='root', password='',
                           database='ai_based_student_monitoring', port=3307)

    cursor = conn.cursor()

    cursor.execute('SELECT * FROM student_info')

    data = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', students=data)


@app.route('/add_student', methods=['POST'])
def add_student():
    # check if admin is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    name = request.form['name']
    moodle_id = request.form['moodle_id']
    email = request.form['email']
    parent_email = request.form['parent_email']
    contact_number = request.form['contact_number']

    conn = pymysql.connect(host='localhost', user='root', password='',
                           database='ai_based_student_monitoring', port=3307)

    cursor = conn.cursor()

    cursor.execute('INSERT INTO student_info (name, moodle_id, email, parent_email, contact_number) VALUES (%s, %s, %s, %s, %s)',
                   (name, moodle_id, email, parent_email, contact_number))

    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/update_student/<id>', methods=['POST'])
def update_student(id):
    # check if admin is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # get form data
    name = request.form['name']
    email = request.form['email']
    parent_email = request.form['parent_email']
    contact_number = request.form['contact_number']

    # update student info in the database
    conn = pymysql.connect(host='localhost', user='root', password='',
                           database='ai_based_student_monitoring', port=3307)
    cursor = conn.cursor()
    cursor.execute('UPDATE student_info SET name=%s, email=%s, parent_email=%s, contact_number=%s WHERE moodle_id=%s',
                   (name, email, parent_email, contact_number, id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_student/<id>', methods=['POST'])
def delete_student(id):
    # check if admin is logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # delete student info from the database
    conn = pymysql.connect(host='localhost', user='root', password='',
                           database='ai_based_student_monitoring', port=3307)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM student_info WHERE moodle_id=%s', id)
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


############################## STUDENT SUBJECT-WISE ATTENDANCE PAGE ################################
@app.route('/studentattendance', methods=['GET'])
def studentattendance():
    return render_template('student_attendance.html')


############################## SPCC SUBJECT ################################
@app.route('/spcc', methods=['POST'])
def spcc():
    # Specify the directory path where the csv files are located
    student_details_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/StudentDetails/"
    spcc_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/Attendance_management/Attendance/spcc/"

    # Get a list of all csv files in the directory
    student_details_files = [os.path.join(student_details_dir, f) for f in os.listdir(
        student_details_dir) if f.endswith('.csv')]
    spcc_files = [os.path.join(spcc_dir, f)
                  for f in os.listdir(spcc_dir) if f.endswith('.csv')]

    # Loop through each csv file and read it using pandas
    dfs = []
    for csv_file in student_details_files + spcc_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)

    # Concatenate the list of dataframes into a single dataframe
    combined_df = pd.concat(dfs)

    # Group the dataframe by "Enrollment" and count the number of occurrences of each enrollment
    grouped_df = combined_df.groupby(
        "Enrollment").size().reset_index(name="Count")

    # Subtract 1 from the "Count" column
    grouped_df["Count"] = grouped_df["Count"] - 1

    # Merge the enrollment with their names
    names_df = combined_df[["Enrollment", "Name"]
                           ].drop_duplicates().set_index("Enrollment")

    # Merge the count and names dataframes
    result_df = pd.merge(grouped_df, names_df, on="Enrollment")

    # Take user input for the total number of classes that have occurred
    total_classes = int(request.form['total_classes'])

    # Add a new column "Total Classes" to the dataframe
    result_df["Total Classes"] = total_classes

    # Calculate the attendance percentage
    result_df["Percentage"] = result_df["Count"] / \
        result_df["Total Classes"] * 100

    # Convert the Enrollment column to integers
    result_df["Enrollment"] = result_df["Enrollment"].astype(int)

    # Reorder the columns as per the desired format
    result_df = result_df[['Enrollment', 'Name',
                           'Count', 'Total Classes', 'Percentage']]

    # Drop the duplicate enrollments to have only one entry per enrollment
    result_df.drop_duplicates(subset="Enrollment", keep="last", inplace=True)

    # Save the final dataframe as a csv file
    result_df.to_csv("attendance_summary_spcc.csv", index=False)

    # Display the output
    return redirect('/table')


@app.route('/table')
def display_table():
    # Load the CSV file into a dataframe
    df = pd.read_csv('attendance_summary_spcc.csv')

    # Render the table HTML template and pass the dataframe as a variable
    return render_template('table.html', data=df.to_html(index=False))


############################## CSS SUBJECT ################################
@app.route('/css', methods=['POST'])
def css():
    # Specify the directory path where the csv files are located
    student_details_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/StudentDetails/"
    spcc_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/Attendance_management/Attendance/css/"

    # Get a list of all csv files in the directory
    student_details_files = [os.path.join(student_details_dir, f) for f in os.listdir(
        student_details_dir) if f.endswith('.csv')]
    spcc_files = [os.path.join(spcc_dir, f)
                  for f in os.listdir(spcc_dir) if f.endswith('.csv')]

    # Loop through each csv file and read it using pandas
    dfs = []
    for csv_file in student_details_files + spcc_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)

    # Concatenate the list of dataframes into a single dataframe
    combined_df = pd.concat(dfs)

    # Group the dataframe by "Enrollment" and count the number of occurrences of each enrollment
    grouped_df = combined_df.groupby(
        "Enrollment").size().reset_index(name="Count")

    # Subtract 1 from the "Count" column
    grouped_df["Count"] = grouped_df["Count"] - 1

    # Merge the enrollment with their names
    names_df = combined_df[["Enrollment", "Name"]
                           ].drop_duplicates().set_index("Enrollment")

    # Merge the count and names dataframes
    result_df = pd.merge(grouped_df, names_df, on="Enrollment")

    # Take user input for the total number of classes that have occurred
    total_classes = int(request.form['total_classes'])

    # Add a new column "Total Classes" to the dataframe
    result_df["Total Classes"] = total_classes

    # Calculate the attendance percentage
    result_df["Percentage"] = result_df["Count"] / \
        result_df["Total Classes"] * 100

    # Convert the Enrollment column to integers
    result_df["Enrollment"] = result_df["Enrollment"].astype(int)

    # Reorder the columns as per the desired format
    result_df = result_df[['Enrollment', 'Name',
                           'Count', 'Total Classes', 'Percentage']]

    # Drop the duplicate enrollments to have only one entry per enrollment
    result_df.drop_duplicates(subset="Enrollment", keep="last", inplace=True)

    # Save the final dataframe as a csv file
    result_df.to_csv("attendance_summary_css.csv", index=False)

    return redirect('/table1')


@app.route('/table1')
def display_table1():
    df = pd.read_csv('attendance_summary_css.csv')

    return render_template('table.html', data=df.to_html(index=False))


############################## AI SUBJECT ################################
@app.route('/ai', methods=['POST'])
def ai():
    # Specify the directory path where the csv files are located
    student_details_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/StudentDetails/"
    spcc_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/Attendance_management/Attendance/ai/"

    # Get a list of all csv files in the directory
    student_details_files = [os.path.join(student_details_dir, f) for f in os.listdir(
        student_details_dir) if f.endswith('.csv')]
    spcc_files = [os.path.join(spcc_dir, f)
                  for f in os.listdir(spcc_dir) if f.endswith('.csv')]

    # Loop through each csv file and read it using pandas
    dfs = []
    for csv_file in student_details_files + spcc_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)

    # Concatenate the list of dataframes into a single dataframe
    combined_df = pd.concat(dfs)

    # Group the dataframe by "Enrollment" and count the number of occurrences of each enrollment
    grouped_df = combined_df.groupby(
        "Enrollment").size().reset_index(name="Count")

    # Subtract 1 from the "Count" column
    grouped_df["Count"] = grouped_df["Count"] - 1

    # Merge the enrollment with their names
    names_df = combined_df[["Enrollment", "Name"]
                           ].drop_duplicates().set_index("Enrollment")

    # Merge the count and names dataframes
    result_df = pd.merge(grouped_df, names_df, on="Enrollment")

    # Take user input for the total number of classes that have occurred
    total_classes = int(request.form['total_classes'])

    # Add a new column "Total Classes" to the dataframe
    result_df["Total Classes"] = total_classes

    # Calculate the attendance percentage
    result_df["Percentage"] = result_df["Count"] / \
        result_df["Total Classes"] * 100

    # Reorder the columns as per the desired format
    result_df = result_df[['Enrollment', 'Name',
                           'Count', 'Total Classes', 'Percentage']]

    # Convert the Enrollment column to integers
    result_df["Enrollment"] = result_df["Enrollment"].astype(int)

    # Drop the duplicate enrollments to have only one entry per enrollment
    result_df.drop_duplicates(subset="Enrollment", keep="last", inplace=True)

    # Save the final dataframe as a csv file
    result_df.to_csv("attendance_summary_ai.csv", index=False)

    return redirect('/table2')


@app.route('/table2')
def display_table2():
    df = pd.read_csv('attendance_summary_ai.csv')

    return render_template('table.html', data=df.to_html(index=False))


############################## MC SUBJECT ################################
@app.route('/mc', methods=['POST'])
def mc():
    # Specify the directory path where the csv files are located
    student_details_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/StudentDetails/"
    spcc_dir = "C:/Users/Namrata Narkhede/PycharmProjects/AI-Based Student Monitoring/Attendance_management/Attendance/mc/"

    # Get a list of all csv files in the directory
    student_details_files = [os.path.join(student_details_dir, f) for f in os.listdir(
        student_details_dir) if f.endswith('.csv')]
    spcc_files = [os.path.join(spcc_dir, f)
                  for f in os.listdir(spcc_dir) if f.endswith('.csv')]

    # Loop through each csv file and read it using pandas
    dfs = []
    for csv_file in student_details_files + spcc_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)

    # Concatenate the list of dataframes into a single dataframe
    combined_df = pd.concat(dfs)

    # Group the dataframe by "Enrollment" and count the number of occurrences of each enrollment
    grouped_df = combined_df.groupby(
        "Enrollment").size().reset_index(name="Count")

    # Subtract 1 from the "Count" column
    grouped_df["Count"] = grouped_df["Count"] - 1

    # Merge the enrollment with their names
    names_df = combined_df[["Enrollment", "Name"]
                           ].drop_duplicates().set_index("Enrollment")

    # Merge the count and names dataframes
    result_df = pd.merge(grouped_df, names_df, on="Enrollment")

    # Take user input for the total number of classes that have occurred
    total_classes = int(request.form['total_classes'])

    # Add a new column "Total Classes" to the dataframe
    result_df["Total Classes"] = total_classes

    # Calculate the attendance percentage
    result_df["Percentage"] = result_df["Count"] / \
        result_df["Total Classes"] * 100

    # Convert the Enrollment column to integers
    result_df["Enrollment"] = result_df["Enrollment"].astype(int)

    # Reorder the columns as per the desired format
    result_df = result_df[['Enrollment', 'Name',
                           'Count', 'Total Classes', 'Percentage']]

    # Drop the duplicate enrollments to have only one entry per enrollment
    result_df.drop_duplicates(subset="Enrollment", keep="last", inplace=True)

    # Save the final dataframe as a csv file
    result_df.to_csv("attendance_summary_mc.csv", index=False)
    return redirect('/table3')


@app.route('/table3')
def display_table3():
    df = pd.read_csv('attendance_summary_mc.csv')

    return render_template('table.html', data=df.to_html(index=False))


############################## OVERALL ATTENDANCE ################################
@app.route('/overall_attendance')
def overall_attendance():
    merged_df = pd.DataFrame()

    for file in glob.glob("attendance_summary*.csv"):
        df = pd.read_csv(file)
        merged_df = pd.concat([merged_df, df], ignore_index=True)

    overall_df = merged_df.groupby(["Enrollment", "Name"]).sum()
    overall_df["Percentage"] = overall_df["Count"] / \
        overall_df["Total Classes"] * 100

    overall_df.to_csv("overall_attendance.csv")

    return redirect('/table4')


@app.route('/table4')
def display_table4():
    df = pd.read_csv('overall_attendance.csv')

    return render_template('table.html', data=df.to_html(index=False))


############################## VISUALIZE ATTENDANCE ################################
@app.route('/visualize')
def visualize():
    # Load data from CSV file
    data = pd.read_csv('overall_attendance.csv')

    # Define filter conditions and plot titles
    filters = {
        'above_90': {'title': 'Attendance Above 90%', 'condition': data['Percentage'] > 90},
        'below_50': {'title': 'Attendance Below 50%', 'condition': data['Percentage'] <= 50},
        'below_30': {'title': 'Attendance Below 30%', 'condition': data['Percentage'] < 30},
        'mid_range': {'title': 'Attendance Between 60% and 80%', 'condition': (data['Percentage'] >= 60) & (data['Percentage'] <= 80)}
    }

    # Generate plots for each filter condition
    plots = {}
    for key, value in filters.items():
        # Filter data based on condition
        filtered_data = data[value['condition']]

        # Create a bar chart
        fig, ax = plt.subplots()
        ax.bar(filtered_data['Name'], filtered_data['Percentage'])
        ax.set_xlabel('Name')
        ax.set_ylabel('Attendance Percentage')
        ax.set_title(value['title'])

        # Render the plot on a canvas outside the main thread's event loop
        canvas = FigureCanvas(fig)
        buffer = BytesIO()
        canvas.print_png(buffer)
        buffer.seek(0)
        image_png = buffer.getvalue()

        # Embed the image in the HTML template
        graph = base64.b64encode(image_png).decode('utf-8')
        plots[key] = graph

        # Clear the plot for the next iteration
        plt.clf()

    # Render the HTML template with the embedded plots
    return render_template('visualize.html', plots=plots)


############################## SEND MAIL TO STUDENT WHOSE ATTENDANCE IS BELOW 75% ################################
def read_csv(file_path):
    data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)
    return data


def send_email(to_email, name):
    from_email = '20102106.namratanarkhede@gmail.com'
    password = 'eimpcpyhdvcdjjhk'
    subject = 'Low Attendance Alert'
    message = f"Dear {name},\n\nYour attendance percentage is below 75%.\n\nPlease make sure to attend all classes.\n\nThanks & Regards,\nAPSIT"
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully!")
    except:
        print("Error: Unable to send email")


def send_email1(to_parent_email):
    from_email = '20102106.namratanarkhede@gmail.com'
    password = 'eimpcpyhdvcdjjhk'
    subject = 'Low Attendance Alert'
    message = f"Dear parent ,\n\nYour ward's attendance percentage is below 75%.\n\nPlease make sure that he/she  attend all classes.\n\nThanks & Regards,\nAPSIT"
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_parent_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_parent_email, msg.as_string())
        print("Email sent successfully!")
    except:
        print("Error: Unable to send email")

# route to check attendance and send email to students and parents


@app.route('/send_mail')
def send_mail():
    overall_attendance_file = 'overall_attendance.csv'
    student_details_file = 'studentdetails.csv'
    overall_attendance_data = read_csv(overall_attendance_file)
    student_details_data = read_csv(student_details_file)
    sent_students = []  # keep track of students to whom emails have been sent
    for i in range(1, len(overall_attendance_data)):
        enrollment = overall_attendance_data[i][0]
        percentage = float(overall_attendance_data[i][-1])
        if percentage < 75:
            for j in range(1, len(student_details_data)):
                if student_details_data[j][1] == enrollment:
                    name = student_details_data[j][0]
                    to_email = student_details_data[j][2]
                    # get parent's email
                    to_parent_email = student_details_data[j][3]
                    send_email(to_email, name)  # send email to student
                    send_email1(to_parent_email)  # send email to parent
                    # add student's name to the list
                    sent_students.append(name)
                    break
    return render_template('Email_send.html', students=sent_students)


if __name__ == '__main__':
    app.run(debug=True)
