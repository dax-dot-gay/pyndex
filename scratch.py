from pyndex import Pyndex

instance = Pyndex("http://localhost:8000", username="admin", password="admin")
with instance.session() as session:
    print(session.users.create("dharr", password="dharr"))
