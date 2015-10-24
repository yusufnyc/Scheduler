import web, bcrypt, random
from web import form

urls=(
	'/', 'Index',
	'/login', 'Login',
	'/register', 'Register',
	'/logout', 'Logout',
	'/school', 'School',
	'/school/join/(\d+)', 'JoinClass',
	'/school/class/(\d+)', 'Class',
	'/school/all', 'SchoolWide'
)
web.config.debug=False
app=web.application(urls, globals())
render=web.template.render('schooltemplates/')
if web.config.get('_session') is None:
	session=web.session.Session(app, web.session.DiskStore('sessions'), initializer={'username': '', 'loggedIn': False, 'school_id': 0})
	web.config._session=session
else:
	session=web.config._session

db=web.database(dbn='mysql', db='hs', user='root', pw='a')

class SchoolWide:
	def GET(self):
		users=db.query('SELECT username FROM users WHERE school_id=$school_id', vars={'school_id': session.school_id})
		return render.all(users)


class JoinClass:
	createClassForm=form.Form(
		form.Textbox('name', description="", class_="form-control center", id="name", placeholder="Class name"),
		form.Textbox('teacher', description="", class_="form-control center", id="teacher", placeholder="Teacher"),
		form.Button('Submit')
	)
	def GET(self, url):
		class_id=web.ctx.fullpath.replace('/school/join/', '')
		print session.get('user_id')
		try:
			schoolId=db.query('SELECT school_id FROM classes WHERE id=$class_id', vars={'class_id': class_id})[0]['school_id']
		except IndexError:
			statusMsg="That class does not exist."
			return render.joinClass(statusMsg)

		students=list(db.query('SELECT student_id FROM class_registrations WHERE class_id=' + class_id))
		alreadyInClass=False
		for student in students:
			if student['student_id']==session.get('user_id'):
				alreadyInClass=True

		if alreadyInClass:
			statusMsg="You are already in that class."
		elif schoolId==session.get('school_id'):
			db.insert('class_registrations', student_id=session.get('user_id'), class_id=class_id)
			statusMsg="Successfully joined class."
		else:
			statusMsg="That class is not part of your school."
		return render.joinClass(statusMsg)


class Index:
	def GET(self):
		if not 'loggedIn' in session:
			session.loggedIn=False
		return render.index(session, db)

class School:
	createClassForm=form.Form(
		form.Textbox('name', description="", class_="form-control center", id="name", placeholder="Class name"),
		form.Password('teacher', description="", class_="form-control center", id="teacher", placeholder="Teacher"),
		form.Button('Submit')
	)
	def GET(self):
		classes=db.query('SELECT * FROM classes WHERE school_id=$school_id', vars={'school_id': session.school_id})
		school=db.query('SELECT * FROM users WHERE school_id=$school_id', vars={'school_id': session.school_id})
		username=session.username
		return render.school(session, school, self.createClassForm, classes)
	def POST(self):
		school=db.query('SELECT * FROM users WHERE school_id=$school_id', vars={'school_id': session.school_id})

		form=self.createClassForm
		if not form.validates():
			return web.seeother('/school')
		else:
			className=form.d.name
			teacher=form.d.teacher
			db.insert('classes', name=className, school_id=session.school_id, teacher=teacher)

			return web.seeother('/school')

class Login:
	loginForm=form.Form(
		form.Textbox('username', description="", class_="form-control center", id="username", placeholder="Username"),
		form.Password('password', description="", class_="form-control center", id="password", placeholder="Password"),
		form.Button('Submit')
	)
	blankForm=form.Form()
	def GET(self):
		if session.loggedIn:
			return web.seeother('/')
		return render.login(self.loginForm, "")
	def POST(self):
		form=self.loginForm
		if not form.validates():
			return render.login(self.loginForm, "The form did not validate.")
		else:
			username=form.d.username
			password=form.d.password
			#hashedPassword=bcrypt.hashpw(password, bcrypt.gensalt())
			# with open('accounts.txt', 'w') as file:
			# 	file.write(username + " " + hashedPassword + "\n")
			pwCorrect=checkAccount(username, password)
			if pwCorrect:
				return web.seeother('/')
			else:
				return render.login(self.loginForm, "incorrect username or password")

class Logout:
	def GET(self):
		session.kill()
		return web.seeother('/')

class Register:
	registerForm=form.Form(
		form.Textbox('username', form.regexp('^[a-zA-Z0-9]{1,20}$', 'Only letters or numbers, <20 characters'), description="", class_="form-control center", id="username", placeholder="Username"),
		form.Password('password', form.regexp('.{6,100}', 'Your password must be at least 6 characters'), description="", class_="form-control center", id="password", placeholder="Password"),
		form.Password('password2', description="", class_="form-control center", placeholder="Confirm password"),
		form.Textbox('email', form.regexp('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', 'Invalid email'), description="", class_="form-control center", id="email", placeholder="Email"),
		form.Textbox('school', description="", class_="form-control center", id="school", placeholder="School"),
		form.Button('Submit'),
		validators=[form.Validator("Passwords didn't match", lambda i: i.password == i.password2)]
	)
	blankForm=form.Form()
	def GET(self):
		if session.loggedIn:
			return web.seeother('/')
		return render.register(self.registerForm, "")
	def POST(self):
		form=self.registerForm
		if not form.validates():
			return render.register(self.registerForm, "The form did not validate.")
		else:
			username=form.d.username
			password=form.d.password
			email=form.d.email
			school=form.d.school
			users=db.select('users')
			for user in users:
				if username==user.username:
					return render.register(self.registerForm, "Username already taken")

			schoolExists=False
			schools=db.select('schools')
			for school_name in schools:
				if school==school_name.name:
					schoolExists=True
			school=form.d.school
			if not schoolExists:
				db.insert('schools', name=school)


			school_id=db.query('SELECT id FROM schools WHERE name=$school', vars={'school': school})[0]['id']
			print school_id
			hashedPassword=bcrypt.hashpw(password, bcrypt.gensalt())
			db.insert('users', username=username, password=hashedPassword, email=email, school=school, school_id=school_id)
			return render.register(self.blankForm, "Success!")

def checkAccount(username, password):
	try:
		user=db.query('SELECT * FROM users WHERE username=$username', vars={'username': username})[0]
	except IndexError:
		return False
	userPass=user['password']
	if bcrypt.hashpw(password, userPass) == userPass:
		session.loggedIn=True
		session.username=user['username']
		session.user_id=user['id']

		session.school=user['school']
		session.school_id=user['school_id']
		return True
	return False

class Class:
	def GET(self, url):
		class_id=web.ctx.fullpath.replace('/school/class/', '')
		student_ids=list(db.query('SELECT student_id FROM class_registrations WHERE class_id=' + class_id))
		students=[]
		statusMsg=""
		allowed=False

		for student_id in student_ids:
			if session.get('user_id')==student_id['student_id']:
				allowed=True
		if allowed==False:
			statusMsg="You are not in this class."
		else:
			for student in student_ids:
				students+=db.query('SELECT * FROM users WHERE id=' + str(student['student_id']))
		return render.classes(db, class_id, students, statusMsg, allowed)



if __name__=="__main__":
	app.run()