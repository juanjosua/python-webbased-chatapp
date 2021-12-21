from werkzeug.security import check_password_hash


class User:
    def __init__(self, username, email, password) -> None:
        self.username = username
        self.email = email
        self.password = password
    
    @staticmethod
    def is_authenticated(self):
        # define logic here if this class used by authenticated
        # and unauthenticated users
        # return true because the user of this class always authenticated
        return True

    @staticmethod
    def is_active(self):
        return True

    @staticmethod
    def is_anonymous(self):
        # the user is not anonymous hence return false
        return False

    def get_id(self):
        return self.username

    def check_password(self, password_input):
        # compared hash password with plain password
        return check_password_hash(self.password, password_input)