clear; clc; close all;

rsam = readtable("ten_hits.csv");

figure(1);

plot( rsam.sample_id_db, rsam.value );
grid on; grid minor;
xlabel("time")
ylabel("RSAM")