int f_1(int a) {
  a = a * a;
  return a;
}

int f_2(int a) {
  a = a + a;
  return a;
}

int main() {
  int a;
  a = 100;
  a = f_1(a) + f_2(a);
  printf("%d", a);
}
