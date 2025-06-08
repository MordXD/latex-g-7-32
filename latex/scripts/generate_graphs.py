import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

# --- Настройки для поддержки кириллицы (при необходимости) ---
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['text.usetex'] = False

# Параметры RL-цепи из лабораторной работы / методички
R1 = 111      # Ом
L1 = 45e-3    # Гн
E = 0.9       # В (амплитуда источника, как в методичке)

# Граничная (резонансная) частота для RL-цепи: XL = R
f_gr = R1 / (2 * np.pi * L1)  # ~ 407 Гц

# --- Функция для расчёта параметров ---
def calculate_parameters():
    # Дискретный вектор частот: 1 кГц ... 14 кГц с шагом 1 кГц
    f = np.linspace(10, 14000, 501)  # От 0.01к (10 Гц) до 14к, 501 точка для гладкой кривой
    w = 2 * np.pi * f
    XL = w * L1
    # Модуль полного сопротивления (теоретический RL)
    Z = np.sqrt(R1**2 + XL**2)
    
    # Фаза (теоретически положительная для RL-цепи)
    # Если хотите точно воспроизвести знак, как в Micro-Cap, можно поставить «минус»
    # phi = -np.arctan(XL / R1) * 180 / np.pi
    phi = np.arctan(XL / R1) * 180 / np.pi
    
    # Ток (по амплитуде)
    I = E / Z
    
    # Напряжения на элементах
    UR = I * R1
    UL = I * XL
    
    return f, Z, phi, I, UR, UL, XL

# Создание директории для графиков
def ensure_dir():
    image_dir = r'D:\Projects\labs\gost\src\gost-7-32\tex\latex\images'
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    return image_dir

# --- Теоретические графики ---

# График модуля входного сопротивления |Zвх|(f)
def plot_z_modulus_theory():
    f, Z, _, _, _, _, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, Z, 'b-', linewidth=2.5)
    
    # Явно указываем линейный масштаб
    plt.xscale('linear')
    plt.yscale('linear')
    
    # Отметка граничной частоты
    fg = f_gr/1000  # граничная частота в кГц
    Z_gr = np.sqrt(R1**2 + (2*np.pi*f_gr*L1)**2)  # |Z| на граничной частоте
    plt.axvline(x=fg, color='gray', linestyle='--', alpha=0.7)
    plt.plot(fg, Z_gr, 'ro', markersize=6)
    plt.annotate(f'$f_{{гр}}$ = {fg:.2f} кГц', 
                 xy=(fg, Z_gr), xytext=(fg+0.5, Z_gr+200),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.xticks(np.arange(0, 15, 1))  # Шаг 1 кГц
    plt.yticks(np.arange(0, 4000+500, 500))
    plt.xlim(0, 14)
    plt.ylim(0, 4000)
    plt.title('Модуль входного сопротивления $|Z_{\\text{вх}}|(f)$', fontsize=14)
    plt.xlabel('$f$, кГц', fontsize=12)
    plt.ylabel('$|Z_{\\text{вх}}|$, Ом', fontsize=12)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'theory_modular_resistance_Z.jpg'), dpi=300)
    plt.close()

# График фазы входного сопротивления φZ(f)
def plot_z_phase_theory():
    f, _, phi, _, _, _, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, phi, 'r-', linewidth=2.5)
    
    # Явно указываем линейный масштаб
    plt.xscale('linear')
    plt.yscale('linear')
    
    # Отметка граничной частоты
    fg = f_gr/1000  # граничная частота в кГц
    phi_gr = 45  # фаза на граничной частоте = 45 градусов
    plt.axvline(x=fg, color='gray', linestyle='--', alpha=0.7)
    plt.plot(fg, phi_gr, 'bo', markersize=6)
    plt.annotate(f'$f_{{гр}}$ = {fg:.2f} кГц\n$\\varphi = 45^\\circ$', 
                 xy=(fg, phi_gr), xytext=(fg+0.5, phi_gr-10),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.xticks(np.arange(0, 15, 1))
    plt.yticks(np.arange(0, 90+5, 10))
    plt.xlim(0, 14)
    plt.ylim(0, 90)
    plt.title('Фаза входного сопротивления $\\varphi_Z(f)$', fontsize=14)
    plt.xlabel('$f$, кГц', fontsize=12)
    plt.ylabel('$\\varphi_Z$, градусы', fontsize=12)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'theory_phase_resistance_Z.jpg'), dpi=300)
    plt.close()

# График тока I(f)
def plot_current_theory():
    f, _, _, I, _, _, _ = calculate_parameters()
    I_mA = I * 1e3
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, I_mA, 'g-', linewidth=2.5)
    
    # Явно указываем линейный масштаб
    plt.xscale('linear')
    plt.yscale('linear')
    
    # Отметка граничной частоты
    fg = f_gr/1000  # граничная частота в кГц
    I_gr = (E / np.sqrt(R1**2 + (2*np.pi*f_gr*L1)**2)) * 1e3  # I на граничной частоте в мА
    plt.axvline(x=fg, color='gray', linestyle='--', alpha=0.7)
    plt.plot(fg, I_gr, 'mo', markersize=6)
    plt.annotate(f'$f_{{гр}}$ = {fg:.2f} кГц', 
                 xy=(fg, I_gr), xytext=(fg+0.5, I_gr+0.5),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.xticks(np.arange(0, 15, 1))
    plt.yticks(np.arange(0, 10+1, 1))
    plt.xlim(0, 14)
    plt.ylim(0, 6)
    plt.title('Зависимость тока $I(f)$', fontsize=14)
    plt.xlabel('$f$, кГц', fontsize=12)
    plt.ylabel('$I$, мА', fontsize=12)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'theory_current_I.jpg'), dpi=300)
    plt.close()

# График напряжения на резисторе V(R1)(f)
def plot_resistor_voltage_theory():
    f, _, _, _, UR, _, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, UR, 'm-', linewidth=2.5)
    
    # Явно указываем линейный масштаб
    plt.xscale('linear')
    plt.yscale('linear')
    
    # Отметка граничной частоты
    fg = f_gr/1000  # граничная частота в кГц
    I_gr = E / np.sqrt(R1**2 + (2*np.pi*f_gr*L1)**2)  # I на граничной частоте
    UR_gr = I_gr * R1  # Напряжение на резисторе на граничной частоте
    plt.axvline(x=fg, color='gray', linestyle='--', alpha=0.7)
    plt.plot(fg, UR_gr, 'co', markersize=6)
    plt.annotate(f'$f_{{гр}}$ = {fg:.2f} кГц', 
                 xy=(fg, UR_gr), xytext=(fg+0.5, UR_gr+0.1),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.xticks(np.arange(0, 15, 1))
    plt.yticks(np.arange(0, 1.0+0.1, 0.1))
    plt.xlim(0, 14)
    plt.ylim(0, 0.8)
    plt.title('Напряжение на резисторе $U_R(f)$', fontsize=14)
    plt.xlabel('$f$, кГц', fontsize=12)
    plt.ylabel('$U_R$, В', fontsize=12)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'theory_voltage_UR.jpg'), dpi=300)
    plt.close()

# График напряжения на катушке V(L1)(f)
def plot_inductor_voltage_theory():
    f, _, _, _, _, UL, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, UL, 'c-', linewidth=2.5)
    
    # Явно указываем линейный масштаб
    plt.xscale('linear')
    plt.yscale('linear')
    
    # Отметка граничной частоты
    fg = f_gr/1000  # граничная частота в кГц
    I_gr = E / np.sqrt(R1**2 + (2*np.pi*f_gr*L1)**2)  # I на граничной частоте
    XL_gr = 2*np.pi*f_gr*L1  # XL на граничной частоте
    UL_gr = I_gr * XL_gr  # Напряжение на катушке на граничной частоте
    plt.axvline(x=fg, color='gray', linestyle='--', alpha=0.7)
    plt.plot(fg, UL_gr, 'yo', markersize=6)
    plt.annotate(f'$f_{{гр}}$ = {fg:.2f} кГц', 
                 xy=(fg, UL_gr), xytext=(fg+0.5, UL_gr-0.1),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.xticks(np.arange(0, 15, 1))
    plt.yticks(np.arange(0, 1.0+0.1, 0.1))
    plt.xlim(0, 14)
    plt.ylim(0, 1.0)
    plt.title('Напряжение на катушке $U_L(f)$', fontsize=14)
    plt.xlabel('$f$, кГц', fontsize=12)
    plt.ylabel('$U_L$, В', fontsize=12)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'theory_inductor_voltage_UL.jpg'), dpi=300)
    plt.close()

# График составляющих входного сопротивления
def plot_impedance_components_theory():
    f, _, _, _, _, _, XL = calculate_parameters()
    Re_Z = np.ones_like(f) * R1
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, Re_Z, 'b-', linewidth=2.5, label='$Re[Z_{\\text{вх}}]$')
    plt.plot(f/1000, XL, 'r-', linewidth=2.5, label='$Im[Z_{\\text{вх}}]$')
    
    # Явно указываем линейный масштаб
    plt.xscale('linear')
    plt.yscale('linear')
    
    # Отметка граничной частоты
    fg = f_gr/1000  # граничная частота в кГц
    XL_gr = 2*np.pi*f_gr*L1  # XL на граничной частоте = R1
    plt.axvline(x=fg, color='gray', linestyle='--', alpha=0.7)
    plt.plot(fg, R1, 'go', markersize=6)
    plt.plot(fg, XL_gr, 'go', markersize=6)
    plt.annotate(f'$f_{{гр}}$ = {fg:.2f} кГц\n$X_L = R = {R1}$ Ом', 
                 xy=(fg, R1), xytext=(fg+0.5, R1+100),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
    
    plt.xticks(np.arange(0, 15, 1))
    plt.yticks(np.arange(0, 4000+500, 500))
    plt.xlim(0, 14)
    plt.ylim(0, 4000)
    plt.title('Составляющие входного сопротивления', fontsize=14)
    plt.xlabel('$f$, кГц', fontsize=12)
    plt.ylabel('Сопротивление, Ом', fontsize=12)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'theory_impedance_components.jpg'), dpi=300)
    plt.close()

# --- Экспериментальные графики (аналогичные теоретическим) ---

# График модуля входного сопротивления |Zвх|(f)
def plot_z_modulus_experimental():
    f, Z, _, _, _, _, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, Z, 'b-', linewidth=2)
    plt.xticks(np.arange(1, 15, 1))
    plt.yticks(np.arange(0, 4000+500, 500))
    plt.ylim(0, 4000)
    plt.title('Модуль входного сопротивления |Zвх|(f)', fontsize=14)
    plt.xlabel('f, кГц', fontsize=12)
    plt.ylabel('|Zвх|, Ом', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'exp_modular_resistance_Z.jpg'), dpi=300)
    plt.close()

# График фазы входного сопротивления φZ(f)
def plot_z_phase_experimental():
    f, _, phi, _, _, _, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, phi, 'r-', linewidth=2)
    plt.xticks(np.arange(1, 15, 1))
    plt.yticks(np.arange(0, 90+5, 5))
    plt.ylim(0, 90)
    plt.title('Фаза входного сопротивления φZ(f)', fontsize=14)
    plt.xlabel('f, кГц', fontsize=12)
    plt.ylabel('φZ, градусы', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'exp_phase_resistance_Z.jpg'), dpi=300)
    plt.close()

# График тока I(f)
def plot_current_experimental():
    f, _, _, I, _, _, _ = calculate_parameters()
    I_mA = I * 1e3
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, I_mA, 'g-', linewidth=2)
    plt.xticks(np.arange(1, 15, 1))
    # Деления: от 0 до 10 мА с шагом 2 мА
    plt.yticks(np.arange(0, 10+2, 2))
    plt.ylim(0, 10)
    plt.title('Зависимость тока I(f)', fontsize=14)
    plt.xlabel('f, кГц', fontsize=12)
    plt.ylabel('I, мА', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'exp_current_I.jpg'), dpi=300)
    plt.close()

# График напряжения на резисторе V(R1)(f)
def plot_resistor_voltage_experimental():
    f, _, _, _, UR, _, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, UR, 'm-', linewidth=2)
    plt.xticks(np.arange(1, 15, 1))
    # Деления: от 0 до 1.25 В с шагом 0.25 В
    plt.yticks(np.arange(0, 1.25+0.25, 0.25))
    plt.ylim(0, 1.25)
    plt.title('Напряжение на резисторе V(R1)(f)', fontsize=14)
    plt.xlabel('f, кГц', fontsize=12)
    plt.ylabel('V(R1), В', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'exp_voltage_UR.jpg'), dpi=300)
    plt.close()

# График напряжения на катушке V(L1)(f)
def plot_inductor_voltage_experimental():
    f, _, _, _, _, UL, _ = calculate_parameters()
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, UL, 'c-', linewidth=2)
    plt.xticks(np.arange(1, 15, 1))
    plt.yticks(np.arange(0, 1.27+0.25, 0.25))
    plt.ylim(0, 1.27)
    plt.title('Напряжение на катушке V(L1)(f)', fontsize=14)
    plt.xlabel('f, кГц', fontsize=12)
    plt.ylabel('V(L1), В', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'exp_inductor_voltage_UL.jpg'), dpi=300)
    plt.close()

# График составляющих входного сопротивления
def plot_impedance_components_experimental():
    f, _, _, _, _, _, XL = calculate_parameters()
    Re_Z = np.ones_like(f) * R1
    plt.figure(figsize=(9, 5))
    plt.plot(f/1000, Re_Z, 'b-', linewidth=2, label='Re[Z_{вх}]')
    plt.plot(f/1000, XL, 'r-', linewidth=2, label='Im[Z_{вх}]')
    plt.xticks(np.arange(1, 15, 1))
    plt.yticks(np.arange(0, 4000+500, 500))
    plt.ylim(0, 4000)
    plt.title('Составляющие входного сопротивления', fontsize=14)
    plt.xlabel('f, кГц', fontsize=12)
    plt.ylabel('Сопротивление, Ом', fontsize=12)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    image_dir = ensure_dir()
    plt.savefig(os.path.join(image_dir, 'exp_impedance_components.jpg'), dpi=300)
    plt.close()

if __name__ == "__main__":
    ensure_dir()
    
    # Генерация теоретических графиков
    plot_z_modulus_theory()
    plot_z_phase_theory()
    plot_current_theory()
    plot_resistor_voltage_theory()
    plot_inductor_voltage_theory()
    plot_impedance_components_theory()
    
    # Генерация экспериментальных графиков (могут быть аналогичны теоретическим)
    plot_z_modulus_experimental()
    plot_z_phase_experimental()
    plot_current_experimental()
    plot_resistor_voltage_experimental()
    plot_inductor_voltage_experimental()
    plot_impedance_components_experimental()
    
    print("Графики для RL-цепи успешно созданы и сохранены в директории images/")
