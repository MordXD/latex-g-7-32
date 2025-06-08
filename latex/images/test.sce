R = [33,-17;-17, 54];
E = [-45; 20];
I = R \ E
I_mesh = R \ E;
printf("Êîíòóðíûå òîêè:\n");
printf("I11 = %.7f À\n", I_mesh(1));
printf("I22 = %.7f À\n", I_mesh(2));