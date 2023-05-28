total_mass = 4000 + 8800
m = total_mass
ve = 2050
fuel_consumption_rate = -129.4
A = ve * (fuel_consumption_rate/total_mass)

t = 0
final_t = 30
v = 0
initial_pos = 0
dt = 0.1

while t < final_t:
  m = 4000 + 8800 * (t*129.4)
  a = A * (m/total_mass)
  v_new = v + a*dt
  t+=dt
  print(v_new)