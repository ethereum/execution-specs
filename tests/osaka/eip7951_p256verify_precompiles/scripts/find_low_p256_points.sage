# Find points on P256 with low x or y coordinates by solving the curve equation
# independently for range of low x and y values.
#
# Can be executed online: https://sagecell.sagemath.org/?q=pmqnkn
#
# Test cases generated:
#
# x_0_y_positive:
#   (0x0000000000000000000000000000000000000000000000000000000000000000, 0x66485c780e2f83d72433bd5d84a06bb6541c2af31dae871728bf856a174f93f4)
# x_0_y_negative:
#   (0x0000000000000000000000000000000000000000000000000000000000000000, 0x99b7a386f1d07c29dbcc42a27b5f9449abe3d50de25178e8d7407a95e8b06c0b)
# x_5_y_positive:
# x_P_plus_5_y_positive:
#   (0x0000000000000000000000000000000000000000000000000000000000000005, 0x459243b9aa581806fe913bce99817ade11ca503c64d9a3c533415c083248fbcc)
# x_5_y_negative:
# x_P_plus_5_y_negative:
#   (0x0000000000000000000000000000000000000000000000000000000000000005, 0xba6dbc4555a7e7fa016ec431667e8521ee35afc49b265c3accbea3f7cdb70433)
# y_1:
# y_P_plus_1:
#   (0x09e78d4ef60d05f750f6636209092bc43cbdd6b47e11a9de20a9feb2a50bb96c, 0x0000000000000000000000000000000000000000000000000000000000000001)


p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
a = -3
b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b

F = GF(p)
aF = F(a)
bF = F(b)

M = 11

for x_int in range(0, M):
    print(f"x = {x_int}:")
    xF = F(x_int)
    rhs = xF**3 + aF*xF + bF

    if rhs.is_square():
        y = rhs.sqrt()
        for yF in [y, -y]:
            print(f"  (0x{int(xF):064x}, 0x{int(yF):064x})")

R.<x> = PolynomialRing(F)
for y_int in range(0, M):
    yF = F(y_int)
    # Solve x^3 + a*x + (b - y^2) == 0 over F_p
    c = bF - yF * yF
    f = x^3 + aF * x + c

    roots = [r for (r, mult) in f.roots()]  # distinct roots over F_p

    print(f"y = {y_int}:")
    for xF in sorted(roots):
        print(f"  (0x{int(xF):064x}, 0x{y_int:064x})")
