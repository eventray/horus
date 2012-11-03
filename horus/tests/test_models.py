# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.tests        import UnitTestBase
from horus.tests.models import Base
from pyramid            import testing
from sqlalchemy.types   import DateTime

from sqlalchemy         import Column

from datetime           import datetime


class TestModel(Base):
    start_date = Column(DateTime)


class TestModels(UnitTestBase):
    def test_tablename(self):
        model = TestModel()
        assert model.__tablename__ == 'test_model'

    def test_json(self):
        model = TestModel()
        model.id = 1
        model.start_date = datetime.now()

        assert model.__json__() == {'id': 1, 'start_date': model.start_date.isoformat()}


class TestActivation(UnitTestBase):
    def test_create_activation_without_valid_until(self):
        from horus.tests.models import Activation

        activation1 = Activation()

        assert activation1.code != None
        assert activation1.valid_until > datetime.utcnow()

    def test_create_activation_with_valid_until(self):
        from horus.tests.models import Activation

        dt = datetime.utcnow()
        activation1 = Activation(valid_until=dt)

        assert activation1.code != None
        assert activation1.valid_until == dt

    def test_get_activation(self):
        from horus.tests.models import Activation

        activation = Activation()
        self.session.add(activation)
        self.session.commit()

        request = testing.DummyRequest()

        new_activation = Activation.get_by_code(request, activation.code)

        assert activation == new_activation

    def test_get_user_activation(self):
        from horus.tests.models import Activation
        from horus.tests.models import User

        user1 = User(username='sontek1', email='sontek@gmail.com')
        user2 = User(username='sontek2', email='sontek+2@gmail.com')
        user1.password = 'password'
        user2.password = 'password'

        activation = Activation()
        user2.activation = activation

        self.session.add(user1)
        self.session.add(user2)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_username(request, 'sontek2')

        new_activation = Activation.get_by_code(request, activation.code)

        assert activation == new_activation
        assert new_user.activation == new_activation


class TestUser(UnitTestBase):
    def test_password_hashing(self):
        from horus.tests.models import User
        user1 = User(username='sontek', email='sontek@gmail.com')
        user1.password = 'password'
        self.session.add(user1)
        self.session.flush()

        assert user1.password != 'password'
        assert user1.salt != None

    def test_acl(self):
        from horus.tests.models import User
        from pyramid.security import Allow

        user1 = User(username='sontek', email='sontek@gmail.com')
        user1.password = 'foo'

        self.session.add(user1)
        self.session.flush()

        assert user1.__acl__ == [(Allow, 'user:%s' % user1.id, 'access_user')]

    def test_get_valid_user(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_user(request, 'sontek', 'temp')

        assert user == new_user

    def test_get_all_users(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        user2 = User(username='sontek2', email='sontek2@gmail.com')
        user2.password = 'temp'
        self.session.add(user)
        self.session.add(user2)
        self.session.commit()

        request = testing.DummyRequest()

        users = User.get_all(request)

        assert len(users.all()) == 2

    def test_get_invalid_user(self):
        from horus.tests.models import User

        user = User(username='sontek1', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_user(request, 'sontek', 'temp')

        assert new_user == None

    def test_get_user_by_id(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_id(request, user.id)

        assert new_user == user

    def test_get_user_by_invalid_id(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_id(request, 2)

        assert new_user == None

    def test_get_user_by_username(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_username(request, 'sontek')

        assert new_user == user

    def test_get_user_by_invalid_username(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_username(request, 'sontek1')

        assert new_user == None

    def test_get_user_by_email(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'password'

        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_email(request, user.email)

        assert new_user == user

    def test_get_user_by_invalid_email(self):
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'password'
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_email(request, 'sontek1@gmail.com')

        assert new_user == None

    def test_get_user_by_activation(self):
        from horus.tests.models import User
        from horus.tests.models import Activation

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'password'
        activation = Activation()
        user.activation = activation

        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_activation(request, activation)

        assert new_user == user

    def test_get_user_by_activation_with_multiple_users(self):
        from horus.tests.models import User
        from horus.tests.models import Activation

        user1 = User(username='sontek1', email='sontek@gmail.com')
        user2 = User(username='sontek2', email='sontek+2@gmail.com')
        user1.password = 'password'
        user2.password = 'password2'
        activation = Activation()
        user2.activation = activation

        self.session.add(user1)
        self.session.add(user2)

        self.session.commit()

        request = testing.DummyRequest()

        new_user = User.get_by_activation(request, activation)

        assert new_user == user2


class TestGroup(UnitTestBase):
    def test_init(self):
        from horus.tests.models import Group
        group = Group(name='foo', description='bar')

        assert group.name == 'foo'
        assert group.description == 'bar'

    def test_get_all(self):
        from horus.tests.models import Group
        from horus.tests.models import User

        user = User(username='sontek', email='sontek@gmail.com')
        user.password = 'temp'
        self.session.add(user)

        group = Group(name='admin', description='group for admins')
        group.users.append(user)
        self.session.add(group)
        self.session.commit()

        request = testing.DummyRequest()

        groups = Group.get_all(request)

        assert len(groups.all()) == 1

    def test_get_by_id(self):
        from horus.tests.models import Group
        from horus.tests.models import User

        group = Group(name='admin', description='group for admins')
        group2 = Group(name='employees', description='group for employees')

        self.session.add(group)
        self.session.add(group2)

        self.session.commit()

        request = testing.DummyRequest()

        group = Group.get_by_id(request, group2.id)

        assert group.name == 'employees'
