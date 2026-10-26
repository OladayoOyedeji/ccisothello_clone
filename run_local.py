import __builtin__
__builtin__.running_locally = True

from mysite import app

if __name__ == "__main__":
    app.run()
