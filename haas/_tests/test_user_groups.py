from haas.model import *
import unittest
class TestModel(unittest.TestCase):
    def test_user_groups(self):
        init_db(True)
        session = Session()
        alice = User('alice','alice')
        bob = User('bob', 'bob')
        admin = Group('admin')
        student = Group('student')
        alice.groups.append(admin)
        alice.groups.append(student)
        session.add(alice)
        self.assertEqual(str(session.query(User).filter(User.label == 'alice').one().groups),"[Group<1 'admin'>, Group<2 'student'>]")
        session.close()

if __name__ == '__main__':
    unittest.main()
