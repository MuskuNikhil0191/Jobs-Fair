import bcrypt

password = "admin"
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(hashed_password)


$2b$12$d21J4i6NNtZr87F8j6OYNuOvlntnqyBVmCikZ8n8zqNW6bvINqfWW