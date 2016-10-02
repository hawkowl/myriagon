def main():
    from .main import build
    app = toga.App('Myriagon', 'net.atleastfornow.myriagon', startup=build)
    app.main_loop()


if __name__ == '__main__':
    main()
