from pyndex import Pyndex

instance = Pyndex("http://localhost:8000", username="admin", password="admin")
with instance.session() as session:
    for package in session.package.all():
        print(package.info.name, package.info.version)
