from . import FEATURES

if "client" in FEATURES:
    from .pyndex_client import main

    if __name__ == "__main__":
        main()
