from user import User

def make_filters(user):
	u = User(user)
	u.make_filters()


def delete_filters(user):
	u = User(user)
	u.delete_filters()