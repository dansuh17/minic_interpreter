void loop(int *a) {
  for (int i = 0; i < 2; i++) {
    a[0] = a[0] + 1;
  }
}

int main(void) {
  int arr[1];
  arr[0] = 0;
  for (int i = 0; i < 5; i++) {
    loop(arr);
  }

  printf("%d", arr[0]);
  return;
}
