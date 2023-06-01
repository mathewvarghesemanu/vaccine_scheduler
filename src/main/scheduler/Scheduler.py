from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import re

'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None

def password_strength_check(password):
    if len(password)<8:
        print("The password should have at least 8 characters")
        return False
    if (password.islower() or password.isupper()): #checking if all upper or all lower
        print("Password should have mixture of uppercase and lowercase letters.")
        return False
    if not (re.search('[a-zA-Z]', password) and re.search('[0-9]', password)):
        print("Password should have mixture of letters and numbers.")
        return False
    if not (re.search('[!@#?]', password)):
        print("Password should include at least one special character, from !, @, #, ?")
        return False
    return True

def create_patient(tokens):
    """
    TODO: Part 1
    """
    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return
    if not password_strength_check(password):
        # print("Password is not strong, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return
    if not password_strength_check(password):
        # print("Password is not strong, try again!")
        return
    
    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False

def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False

def login_patient(tokens):
    # login_patient <username> <password>
    """
    TODO: Part 1
    """
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if patient is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_patient = patient



def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    """
    TODO: Part 2
    """
    #  check 1: check if there is current logged-in user
    global current_caregiver
    global current_patient

    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        query_date = datetime.datetime(year, month, day)
        caregiver_availability = "SELECT Caregivers.Username FROM Caregivers, Availabilities WHERE Availabilities.Username = Caregivers.Username AND Availabilities.Time = (%d) ORDER BY Caregivers.Username"
        
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        cursor.execute(caregiver_availability, query_date)
        
        print("Caregiver Name")
        for item in cursor:
            print(str(item[0]))

        print("\n")

    except pymssql.Error as e:
        print("Cannot search for caregiver schedule")
        print("Please try again!")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Enter a valid date")
        print("Please try again!")
        return
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()

    try:
        vaccine_availability = "SELECT Name, Doses FROM Vaccines"

        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        cursor.execute(vaccine_availability)

        print("Vaccine Name" , " " , "Number of Doses")
        for item in cursor:
            print(str(item[0]), " " , str(item[1]))

        conn.commit()

    except pymssql.Error as e:
        print("Vaccine schedule cannot be fetched")
        print("Please try again!")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()
    
    print("\n")
    print("Caregiver availability printed successfully!")
    print("\n")


def reserve(tokens):
    """
    TODO: Part 2
    """
    # checking length of token to make sure that we got all the arguments needed for making a reservation
    if len(tokens) != 3:
        print("Please try again!")
        return
    
    #  checking whether patient logged in
    global current_patient
    if current_patient == None:
        print("Please login as patient!")
        return
    
    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    d = datetime.datetime(year, month, day)

    vaccine_name = tokens[2]

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()
    
    # find all free caregivers in input date
    caregiver_available = "SELECT Username FROM Availabilities WHERE Time = (%s) ORDER BY Username"
    selected_caregiver = ""
    try:
        cursor.execute(caregiver_available, (d))
        caregiver_available = cursor.fetchone()

    except Exception as e:
        print("Error checking for caregiver availability")
        print("Error:", e)
        return 0
    finally:
        cm.close_connection()

    if caregiver_available == None:
        print("No Caregiver is available!")
        return 0
    else:
        selected_caregiver =  caregiver_available[0]

    # Checking for vaccine availability
    vaccine_available = "SELECT Name, Doses FROM Vaccines WHERE Name = (%s)"
    try:

        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        cursor.execute(vaccine_available, vaccine_name)
        vaccine_available = cursor.fetchone()

    except Exception as e:
        print("Error checking vaccine availability")
        print("Error:", e)
        return
    finally:
        cm.close_connection()

    
    if vaccine_available == None or vaccine_available[1] == 0:
        print("Not enough available doses!")
        return 0
    
    #idea is to get serial numbers for appointment ID
    appointment_id_fetch_query = "SELECT MAX(appointment_id) FROM Appointments"
    try:

        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        
        cursor.execute(appointment_id_fetch_query)
        latest_appointment_id = cursor.fetchone()

        if latest_appointment_id[0] == None:
            current_appointment_id= 1    
        else: 
            current_appointment_id= latest_appointment_id[0]+ 1

    except pymssql.Error:
        print("Error assigning appointment ID")
        return 0    
    finally:
        cm.close_connection()

    print("Appointment ID:", current_appointment_id, "\n","Caregiver Username:",selected_caregiver)

    #Insert data to appointments table
    try:
        reserve_appointment_query = "INSERT INTO Appointments VALUES (%s, %s, %s, %s, %s)"

        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        cursor.execute(reserve_appointment_query, (current_appointment_id, d, vaccine_name, current_patient.username,selected_caregiver ))
        conn.commit()

    except pymssql.Error:
        print("Error occurred when updating appointments table")
        raise
    finally:
        cm.close_connection()

    #make caregiver unavailable
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    try:
        delete_caregiver_availability = "DELETE FROM Availabilities WHERE Time = (%d) AND Username = (%s)"

        cursor.execute(delete_caregiver_availability, (date, selected_caregiver))
        conn.commit()

    except pymssql.Error as e:
        print("Db-Error:", e)
        return 0
    except Exception as e:
        print("Error occurred when removing caregiver availability for the day")
        print("Error:", e)
        return 0
    finally:
        cm.close_connection()
    
    #remove scheduled vaccine
    try:
        #create vaccine object
        vaccine_reservation = Vaccine(vaccine_name,0)
        vaccine_reservation.get()
        vaccine_reservation.decrease_available_doses(1)

    except pymssql.Error as e:
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when decreasing doses")
        print("Error:", e)
        return
    finally:
        cm.close_connection()
    
    print('Reservation completed successfully!')


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    '''
    TODO: Part 2
    '''
    global current_caregiver
    global current_patient

    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return 0
    
    if len(tokens) != 1:
        print("Please try again!")
        return 0

    try:
        if current_caregiver: 

            cm = ConnectionManager()
            conn = cm.create_connection()
            cursor = conn.cursor()

            fetch_caregiver_appointment_query = "SELECT appointment_id, patient_name, vaccine_name, time FROM Appointments WHERE caregiver_name = (%s) ORDER BY appointment_id"
            
            try:
                cursor.execute(fetch_caregiver_appointment_query, (current_caregiver.username))

                for item in cursor:
                    print(str(item[0]) + " " + str(item[1]) + " " + str(item[2]) + " " + str(item[3]))

            except pymssql.Error:
                print("Error! Cannot fetch caregiver appointments")
                return 0
            finally:
                cm.close_connection()

        else:
            if current_patient: 

                cm = ConnectionManager()
                conn = cm.create_connection()
                cursor = conn.cursor()

                fetch_patient_appointment_query = "SELECT appointment_id, caregiver_name, vaccine_name, time FROM Appointments WHERE patient_name = (%s) ORDER BY appointment_id"
                
                try:
                    cursor.execute(fetch_patient_appointment_query, (current_patient.username))

                    for item in cursor:
                        print(str(item[0]) + " " + str(item[1]) + " " + str(item[2]) + " " + str(item[3]))
                except pymssql.Error:
                    print("Error! Cannot fetch patients' appointments")
                    return 0
                finally:
                    cm.close_connection()

    except Exception as e:
        print("Error:", e)
        return 0


def logout(tokens):
    """
    TODO: Part 2
    """
    if len(tokens) != 1:
        print("Please try again!")
        return 0
    
    global current_caregiver
    global current_patient

    if current_patient == None and current_caregiver == None:
        print("Please login first!")
        return 0
    
    else:
        current_caregiver = None
        current_patient = None
        print("Successfully logged out!")


def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        # response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0].lower()
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
