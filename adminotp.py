import random

def adotp():
    u_c = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    l_c = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    adminotp = ''
    for i in range(2):  # 2 sets of OTP characters: Uppercase letter + number + Lowercase letter
        adminotp += random.choice(u_c)  # Random uppercase letter
        adminotp += str(random.randint(0, 9))  # Random digit
        adminotp += random.choice(l_c)  # Random lowercase letter
    return adminotp
