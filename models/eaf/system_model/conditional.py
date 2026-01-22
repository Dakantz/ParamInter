# refactored from https://github.com/SayYoungMan/EAF_modelling/blob/main/eaf.m
## LICENSE
# MIT License

# Copyright (c) 2021 SayYoungMan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, pt.expRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import torch as pt
from dataclasses import dataclass, field, asdict


def ensure_tensor(x: pt.Tensor | float):
    if isinstance(x, pt.Tensor):
        return x
    else:
        return pt.tensor(x).float()


@dataclass
class EAFParameters:
    # Time slice
    ts: float = 1 / 10  # 10**-2 s

    # Total operating time in s
    secs: float = 2500

    # Takeout interval in s
    out: float = 600

    # ---------- DRI Settings -----------

    # Temperature of DRI in K
    T_DRI: float = 559.32

    # DRI mass addition rate in kg/s
    DRI_add: float = 346656 / 3600

    # DRI mass fraction
    MX_Fe_DRI: float = 0.88548
    MX_C_DRI: float = 0.016336
    MX_SiO2_DRI: float = 0.0570
    MX_Al2O3_DRI: float = 0.03705
    MX_CaO_DRI: float = 0.00136
    MX_MgO_DRI: float = 0.0008
    MX_MnO_DRI: float = 0.0001
    MX_P2O5_DRI: float = 0.00186

    # --------- Scrap Settings -----------

    # Temperature of scrap in K
    T_scr: float = 559.32

    # DRI mass addition rate in kg/s
    scr_add: float = 80000.0 / 3600

    # DRI mass fraction
    MX_Fe_scr: float = 0.9705
    MX_C_scr: float = 0.004
    MX_Si_scr: float = 0.006
    MX_Cr_scr: float = 0.002
    MX_P_scr: float = 0.0005
    MX_Mn_scr: float = 0.006
    MX_comb_scr: float = 0.011

    # ---------- Slag Settings -----------

    # Temperature of slag in K
    T_slg: float = 300

    # Slag mass addition rate in kg/s
    slg_add: float = 3

    # Slag mass fraction
    MX_CaO_slg: float = 0.573
    MX_MgO_slg: float = 0.415
    MX_SiO2_slg: float = 0.007
    MX_Al2O3_slg: float = 0.005

    # --------- Reactor Geometry ---------
    r_eafout: float = 3.3
    r_eafin: float = 2.45
    r_hole: float = 0.3
    r_electrode: float = 0.3
    h_eafup: float = 2.9
    h_eaflow: float = 1.0
    h_electrode: float = 1.0
    d1: float = 0.30
    d2: float = 0.45

    # ---------- Other Settings ----------

    # Carbon Injection Rate (kg/s)
    C_inj: float = 0.3

    # Ferro-Manganese Injection Rate (kg/s)
    FM_inj: float = 1.5

    MX_Mn_FM: float = 0.78
    MX_C_FM: float = 0.07
    MX_P_FM: float = 0.002
    MX_Si_FM: float = 0.003
    MX_Fe_FM: float = 0.145

    # Oxygen Lance Rate (kg/s)
    O2_lance: float = 4

    # O2 for post combustion (kg/s)
    O2_post: float = 1

    # Power of arc (kW)
    P_arc: float = 40000

    # EAF mass capacity (kg)
    m_EAF: float = 105000

    # Cooling water flowrate (mol/s)
    phi1: float = 80 / 0.018
    phi2: float = 150 / 0.018

    #:float ======================= Initial Parameters:float =========================

    # ------------- Initial mass (kg) --------------

    # Solid metal initial mass
    m_Fe_sSc: float = 1203
    m_C_sSc: float = 17.1
    m_Cr_sSc: float = 0.42
    m_Mn_sSc: float = 16.07
    m_P_sSc: float = 0.14
    m_SiO2_sSc: float = 52.1
    m_Al2O3_sSc: float = 33.9
    m_CaO_sSc: float = 1.67
    m_MgO_sSc: float = 0.98
    m_MnO_sSc: float = 0.123
    m_P2O5_sSc: float = 2.28
    m_Si_sSc: float = 1.7
    m_comb_sSc: float = 5.6

    # Liquid metal initial mass
    m_Fe_lSc: float = 64411
    m_C_lSc: float = 314
    m_Cr_lSc: float = 26.3
    m_Mn_lSc: float = 617
    m_P_lSc: float = 4.5
    m_Si_lSc: float = 122.7

    # Solid slag initial mass
    m_CaO_sSl: float = 64.2
    m_MgO_sSl: float = 46.5
    m_SiO2_sSl: float = 2
    m_Al2O3_sSl: float = 1.4

    # Liquid slag initial mass
    m_SiO2_lSl: float = 3229
    m_Al2O3_lSl: float = 2153
    m_CaO_lSl: float = 1119
    m_MgO_lSl: float = 795
    m_MnO_lSl: float = 960
    m_P2O5_lSl: float = 115.3
    m_Cr2O3_lSl: float = 2.19
    m_FeO_lSl: float = 3195

    # Gas initial mass
    m_H2O: float = 182
    m_O2: float = 414
    m_CO: float = 1388
    m_CO2: float = 190

    # Initial mass of injected carbon
    m_CL: float = 0.792

    # mass ratios liquid slag
    MX_SiO2_lSl: float = 0
    MX_Al2O3_lSl: float = 0
    MX_CaO_lSl: float = 0
    MX_MgO_lSl: float = 0
    MX_MnO_lSl: float = 0
    MX_P2O5_lSl: float = 0
    MX_Cr2O3_lSl: float = 0
    MX_FeO_lSl: float = 0

    # mass ratios liquid metal
    MX_Fe_lSc: float = 0
    MX_C_lSc: float = 0
    MX_Cr_lSc: float = 0
    MX_Mn_lSc: float = 0
    MX_P_lSc: float = 0
    MX_Si_lSc: float = 0

    # ------------- Initial temp. (K) --------------

    T_sSc: float = 791
    T_lSc: float = 2079
    T_sSl: float = 1051
    T_lSl: float = 1997
    T_gas: float = 1854
    T_wall: float = 328
    T_roof: float = 339

    # -------------- Initial Geometry --------------

    # Densities (kg/m3)
    rho_sSc: float = 900  # Kurz and Fisher 2005
    rho_lSc: float = 7000
    rho_lSl: float = (
        3500  # Self-compacting concrete: materials properties and applications Siddique (2020) Table 10.1
    )
    rho: float = 7000

    h_sSc2: float = 0

    # ----------------- Others ---------------------

    # Initial Pressure
    p_gas: float = 1.2  # atm
    rp: float = 0  # Relative pressure

    # Initial Radiosity
    J_roof: float = 0
    J_wall: float = 0
    J_sSc: float = 0
    J_lSc: float = 0

    # =========================== Constants ==============================

    # ------------ Molar Mass (kg/mol) -------------
    M_Fe: float = 0.055845
    M_C: float = 0.0120107
    M_Si: float = 0.0280855
    M_FeO: float = 0.071844
    M_SiO2: float = 0.06008
    M_O2: float = 0.032
    M_CO: float = 0.02801
    M_CO2: float = 0.04401
    M_CH4: float = 0.01604
    M_Cr: float = 0.051996
    M_Mn: float = 0.054938
    M_P: float = 0.030976
    M_MnO: float = 0.0709374
    M_Cr2O3: float = 0.15199
    M_P2O5: float = 0.283886 / 2
    M_CaO: float = 0.05608
    M_MgO: float = 0.040304
    M_C9H20: float = 0.1282
    M_gas: float = 0.035
    M_Al2O3: float = 0.10196
    M_Al: float = 0.02698
    M_H2O: float = 0.01802
    M_sSl: float = 0.0484
    M_lSl: float = 0.0509

    # ------------ Reaction rate constant -------------

    kd_CL: float = 15  # s-1
    kd_CD: float = 35  # kg/s
    kd_C1: float = 60
    kd_C2: float = 55
    kd_Mn1: float = 20
    kd_Mn2: float = 10
    kd_Mn: float = 75
    kd_Si1: float = 144
    kd_Si2: float = 250
    kd_Cr1: float = 3
    kd_Cr2: float = 1
    kd_P: float = 35
    kd_comb: float = 0.1  # s-1

    # ----------- Thermodynamic Properties ------------

    # Heat capacities (kJ/mol K)
    Cp_C: float = 0.02092  # at 1800K (from NIST)
    Cp_H2O: float = 0.075
    Cp_sSc: float = 0.039
    Cp_lSc: float = 0.047
    Cp_sSl: float = 0.025
    Cp_lSl: float = 0.047
    Cp_gas: float = 0.030
    Cp_roof: float = 0.65  # kJ/kg K
    Cp_wall: float = 0.96  # kJ/kg K

    # Latent heat of fusion (kJ/mol)
    lambda_C: float = 117
    lambda_sSc: float = 15.4
    lambda_sSl: float = 12.66

    # Enthalpies of formation (kJ/mol)
    dH_FeO: float = -243
    dH_FeS: float = 0
    dH_CO: float = -117
    dH_CO2: float = -396
    dH_CS: float = -27
    dH_MnS: float = -20
    dH_MnO: float = -385
    dH_SiS: float = -132
    dH_SiO2: float = -946
    dH_SiO2S: float = -45
    dH_CrS: float = -42
    dH_Cr2O3: float = -1142
    dH_PS: float = -29
    dH_P2O5: float = -2940
    dH_H2O: float = -247
    dH_CH4: float = -91
    dH_C9H20: float = -228.3

    # ------------ Conduction Constants ---------------

    # Heat transfer coeffs kW/m**2K
    K_therm1: float = 0.2
    K_therm2: float = 0.2
    K_therm3: float = 0.05
    K_therm4: float = 57.5  # kW/K
    K_therm5: float = 0.2
    K_therm6: float = 0.08
    K_therm7: float = 22.5  # kW/K
    K_therm8: float = 22.5  # kW/K

    # Area coeffs m**2/kg
    K_area1: float = 0.008
    K_area2: float = 0.12
    K_area3: float = 0.12
    K_area5: float = 0.12
    K_area6: float = 0.12

    # Thermal conductance coeff. kW/K
    K_water1: float = 12
    K_water2: float = 20
    K_water3: float = 10
    K_water4: float = 5
    K_water5: float = 0.05

    # ------------ Radiation Constants ---------------

    # Stefan Boltzmann Constant
    sig: float = 5.67e-08  # W.m-2.K-4s-1

    # Emissivity
    ep1: float = 0.85  # Roof
    ep2: float = 0.85  # Wall
    ep3: float = 0.80  # sSc
    ep4: float = 0.40  # lSc

    # ------------ Constant Temperatures --------------

    T_air: float = 298
    T_melt: float = 1809
    T_water: float = 298

    # ------------------- Others ----------------------

    # Distribution of lanced oxygen
    K_O2CO: float = 0.05
    K_O2CO2: float = 0.15
    K_O2Cr2O3: float = 0.015
    K_O2FeO: float = 0.75
    K_O2SiO2: float = 0.035

    # Vent
    hd: float = 0.65
    K_U: float = 6.44
    u1: float = 20
    u2: float = 0.3

    V_gas: float = 45

    # Electrode
    R_tip: float = 0.02
    R_side: float = 10
    A_side: float = 35
    I_arc: float = 30

    A_bath: float = 0
    A_eaf: float = 0

    h_lSc: float = 0
    h_lSl: float = 0
    h_sSc2: float = 0

    d_conein: float = 0
    d_coneout: float = 0
    V_sSc: float = 0
    h_cone: float = 0
    h_arc: float = 0
    h_wall: float = 0
    A1: float = 0
    A2: float = 0
    A4: float = 0
    K_sSclSc: float = 0

    m_lSc: float = 0
    m_lSl: float = 0
    m_sSc: float = 0
    m_sSl: float = 0

    y_name: str = "MX_C_lSc"
    x_names: tuple[str] = ("O2_lance", "P_arc", "O2_post", "C_inj", "FM_inj", "DRI_add")
    observer_names: tuple[str] = ("MX_SiO2_lSl", "MX_FeO_lSl", "T_lSl", "T_lSc")

    def __init__(self):
        self.m_sSc = (
            self.m_Fe_sSc
            + self.m_C_sSc
            + self.m_Cr_sSc
            + self.m_Mn_sSc
            + self.m_P_sSc
            + self.m_SiO2_sSc
            + self.m_Al2O3_sSc
            + self.m_CaO_sSc
            + self.m_MgO_sSc
            + self.m_MnO_sSc
            + self.m_P2O5_sSc
            + self.m_Si_sSc
            + self.m_comb_sSc
        )
        # Total mass of solid metal [kg]
        self.m_lSc = (
            self.m_Fe_lSc
            + self.m_C_lSc
            + self.m_Cr_lSc
            + self.m_Mn_lSc
            + self.m_P_lSc
            + self.m_Si_lSc
        )

        self.m_lSl = (
            self.m_SiO2_lSl
            + self.m_Al2O3_lSl
            + self.m_CaO_lSl
            + self.m_MgO_lSl
            + self.m_MnO_lSl
            + self.m_P2O5_lSl
            + self.m_Cr2O3_lSl
            + self.m_FeO_lSl
        )
        self.A_bath = pt.pi * self.r_eafin**2
        self.A_eaf = pt.pi * self.r_eafout**2

        # height of liquid metal
        self.h_lSc = (self.m_lSc / self.rho_lSc) / self.A_bath

        # height of liquid slag
        self.h_lSl = (self.m_lSl / self.rho_lSl) / self.A_bath

        # height of solid metal
        # V_free = (A_bath*h_eaflow) - (m_lSc/rho_lSc) - (m_lSl/rho_lSl)
        # if V_free >= m_sSc/rho_sSc
        #     h_sSc1 = 0
        #     h_sSc2 = (m_sSc/rho_sSc) / A_bath
        # else
        #     h_sSc1 = ((m_sSc/rho_sSc) - V_free) / A_eaf
        #     h_sSc2 = V_free / A_bath
        # end
        #

        self.h_sSc2 = 0
        self.d_conein = self.r_eafin * 2
        self.d_coneout = self.r_eafout * 2

        self.V_sSc = self.m_sSc / self.rho_sSc
        self.h_cone = self.V_sSc / (
            pt.pi * self.r_eafout**2
            - (1 / 3)
            * pt.pi
            * (self.r_eafin**2 + self.r_eafin * self.r_eafout + self.r_eafout**2)
        )
        self.h_sSc1 = self.h_cone

        # Arc height
        self.h_arc = self.h_eafup - self.h_electrode - (self.h_sSc2 - self.h_cone)

        # height of wall
        self.h_wall = (
            self.h_eafup + self.h_eaflow - self.h_sSc1 - self.h_lSc - self.h_lSl
        )

        # Areas of roof and wall
        self.A1 = (pt.pi * self.r_eafout**2) - (pt.pi * self.r_hole**2)  # roof
        self.A2 = 2 * pt.pi * self.r_eafout * self.h_wall  # wall
        self.A4 = pt.pi * self.r_eafin**2

        # ----------------- Others ---------------------

        # Exposure constant
        self.K_sSclSc = (
            0.5
            * pt.tanh(
                ensure_tensor(
                    5 * (self.h_lSc - self.h_sSc1 - self.h_sSc2 + self.h_cone)
                )
            )
            + 0.5
        )

    def prep(self, x_names: list[str] = None, y_name: str = None):
        if x_names is None:
            x_names = self.x_names
        if y_name is None:
            y_name = self.y_name
        for x_name in x_names:
            x_var = getattr(self, x_name)
            if isinstance(x_var, pt.Tensor):
                x_var = x_var.float()
            else:
                x_var = float(x_var)
            # print(x_name, x_var)
            x_var = pt.tensor(x_var, requires_grad=True)
            setattr(self, x_name, x_var)
        y_var = getattr(self, x_name)
        y_var = pt.tensor(y_var)
        setattr(self, y_name, y_var)

    def getfloat(self, key: str):
        param = getattr(self, key)
        if isinstance(param, pt.Tensor):
            return param.detach().numpy()[()]
        else:
            return param

    def recalc_MX_lSc(self):
        self.MX_Fe_lSc = self.m_Fe_lSc / self.m_lSc
        self.MX_C_lSc = self.m_C_lSc / self.m_lSc
        self.MX_Cr_lSc = self.m_Cr_lSc / self.m_lSc
        self.MX_Mn_lSc = self.m_Mn_lSc / self.m_lSc
        self.MX_P_lSc = self.m_P_lSc / self.m_lSc
        self.MX_Si_lSc = self.m_Si_lSc / self.m_lSc


class TakeoutInput:
    def __init__(self, params: EAFParameters, x_name: str) -> None:
        x_var: pt.Tensor = getattr(params, x_name)
        assert isinstance(x_var, pt.Tensor), ("variable must be tensor!", x_name, x_var)

        self.value: float = x_var.detach().numpy()[()]
        self.name = x_name
        self.sensitivity = x_var.grad.detach().numpy()[()]
        x_var.grad = None


class TakeoutAnalysis:
    def __init__(self, params: EAFParameters, time: float) -> None:
        y_var: pt.Tensor = getattr(params, params.y_name)
        assert isinstance(y_var, pt.Tensor), (
            "variable must be tensor!",
            params.y_name,
            y_var,
        )
        y_var.backward(retain_graph=True)
        self.y_var_value = y_var.detach().numpy()[()]
        self.y_var_name = params.y_name
        self.x_vars: dict[str, TakeoutInput] = {
            x_var_name: TakeoutInput(params, x_var_name)
            for x_var_name in params.x_names
        }
        self.observations: dict[str, float] = {
            key: params.getfloat(key) for key in params.observer_names
        }
        self.time = time

        for k, v in params.__dict__.items():
            if isinstance(v, pt.Tensor):
                v.grad = None

    def to_dict(self) -> dict[str, float]:
        return {
            **{self.y_var_name: self.y_var_value},
            **{k: v for k, v in self.observations.items()},
            **{k: v.value for k, v in self.x_vars.items()},
            **{f"{k}_sensitivity": v.sensitivity for k, v in self.x_vars.items()},
            **{"time": self.time},
        }


class EAFModel:
    def __init__(self, _parameters: EAFParameters) -> None:
        self.p = _parameters
        self.out_states: list[TakeoutAnalysis] = []
        self.gas_temp: pt.Tensor = pt.zeros(self.p.secs)
        self.sSc_temp: pt.Tensor = pt.zeros(self.p.secs)
        self.sSl_temp: pt.Tensor = pt.zeros(self.p.secs)
        self.lSc_temp: pt.Tensor = pt.zeros(self.p.secs)
        self.lSl_temp: pt.Tensor = pt.zeros(self.p.secs)
        self.steel_Fe: pt.Tensor = pt.zeros(self.p.secs)
        self.m_solid: pt.Tensor = pt.zeros(self.p.secs)
        self.m_liquid: pt.Tensor = pt.zeros(self.p.secs)
        self.m_solid_slag: pt.Tensor = pt.zeros(self.p.secs)
        self.m_liquid_slag: pt.Tensor = pt.zeros(self.p.secs)
        self.rel_pres: pt.Tensor = pt.zeros(self.p.secs)
        self.t: pt.Tensor = pt.arange(0, self.p.secs)
        self.step: int = 0
        self.reset()

    def reset(self):
        # ------------------------- Arrays for graph ------------------------
        self.gas_temp = pt.zeros(self.p.secs)
        self.sSc_temp = pt.zeros(self.p.secs)
        self.sSl_temp = pt.zeros(self.p.secs)
        self.lSc_temp = pt.zeros(self.p.secs)
        self.lSl_temp = pt.zeros(self.p.secs)
        self.steel_Fe = pt.zeros(self.p.secs)
        self.m_solid = pt.zeros(self.p.secs)
        self.m_liquid = pt.zeros(self.p.secs)
        self.m_solid_slag = pt.zeros(self.p.secs)
        self.m_liquid_slag = pt.zeros(self.p.secs)
        self.rel_pres = pt.zeros(self.p.secs)
        self.t = pt.arange(0, self.p.secs)
        self.step = 0
        self.out_states = []


def step_eaf(s: EAFModel):
    s.p.m_Cr_sSc = pt.relu(ensure_tensor(s.p.m_Cr_sSc))
    s.p.m_Cr_lSc = pt.relu(ensure_tensor(s.p.m_Cr_lSc))
    s.p.m_Fe_sSc = pt.relu(ensure_tensor(s.p.m_Fe_sSc))
    s.p.m_Fe_lSc = pt.relu(ensure_tensor(s.p.m_Fe_lSc))
    s.p.m_Mn_sSc = pt.relu(ensure_tensor(s.p.m_Mn_sSc))
    s.p.m_Mn_lSc = pt.relu(ensure_tensor(s.p.m_Mn_lSc))
    s.p.m_P_sSc = pt.relu(ensure_tensor(s.p.m_P_sSc))
    s.p.m_P_lSc = pt.relu(ensure_tensor(s.p.m_P_lSc))
    s.p.m_Si_sSc = pt.relu(ensure_tensor(s.p.m_Si_sSc))
    s.p.m_Si_lSc = pt.relu(ensure_tensor(s.p.m_Si_lSc))
    s.p.m_C_sSc = pt.relu(ensure_tensor(s.p.m_C_sSc))
    s.p.m_C_lSc = pt.relu(ensure_tensor(s.p.m_C_lSc))
    s.p.m_Al2O3_sSc = pt.relu(ensure_tensor(s.p.m_Al2O3_sSc))
    s.p.m_Al2O3_lSl = pt.relu(ensure_tensor(s.p.m_Al2O3_lSl))
    s.p.m_CaO_sSc = pt.relu(ensure_tensor(s.p.m_CaO_sSc))
    s.p.m_CaO_lSl = pt.relu(ensure_tensor(s.p.m_CaO_lSl))
    s.p.m_SiO2_sSc = pt.relu(ensure_tensor(s.p.m_SiO2_sSc))
    s.p.m_SiO2_lSl = pt.relu(ensure_tensor(s.p.m_SiO2_lSl))
    s.p.m_MgO_sSc = pt.relu(ensure_tensor(s.p.m_MgO_sSc))
    s.p.m_MgO_lSl = pt.relu(ensure_tensor(s.p.m_MgO_lSl))
    s.p.m_MnO_sSc = pt.relu(ensure_tensor(s.p.m_MnO_sSc))
    s.p.m_MnO_lSl = pt.relu(ensure_tensor(s.p.m_MnO_lSl))
    s.p.m_P2O5_sSc = pt.relu(ensure_tensor(s.p.m_P2O5_sSc))
    s.p.m_P2O5_lSl = pt.relu(ensure_tensor(s.p.m_P2O5_lSl))
    # ====================== Mole, Mass Fraction =====================

    # ------------ Solid Metal ------------

    # Total mass of solid metal [kg]
    s.p.m_sSc = (
        s.p.m_Fe_sSc
        + s.p.m_C_sSc
        + s.p.m_Cr_sSc
        + s.p.m_Mn_sSc
        + s.p.m_P_sSc
        + s.p.m_SiO2_sSc
        + s.p.m_Al2O3_sSc
        + s.p.m_CaO_sSc
        + s.p.m_MgO_sSc
        + s.p.m_MnO_sSc
        + s.p.m_Si_sSc
        + s.p.m_comb_sSc
        + s.p.m_P2O5_sSc
    )

    # Total mole of solid metal [mol]
    XM_sSc = (
        (s.p.m_Fe_sSc / s.p.M_Fe)
        + (s.p.m_C_sSc / s.p.M_C)
        + (s.p.m_Cr_sSc / s.p.M_Cr)
        + (s.p.m_Mn_sSc / s.p.M_Mn)
        + (s.p.m_P_sSc / s.p.M_P)
        + (s.p.m_SiO2_sSc / s.p.M_SiO2)
        + (s.p.m_Al2O3_sSc / s.p.M_Al2O3)
        + (s.p.m_CaO_sSc / s.p.M_CaO)
        + (s.p.m_MgO_sSc / s.p.M_MgO)
        + (s.p.m_MnO_sSc / s.p.M_MnO)
        + (s.p.m_Si_sSc / s.p.M_Si)
        + (s.p.m_comb_sSc / s.p.M_C9H20)
        + (s.p.m_P2O5_sSc / s.p.M_P2O5)
    )

    # Mole fractions of compounds in solid metal
    # X_Fe_sSc = (s.p.m_Fe_sSc / s.p.M_Fe) / XM_sSc
    # X_C_sSc = (s.p.m_C_sSc / s.p.M_C) / XM_sSc
    # X_Cr_sSc = (s.p.m_Cr_sSc / s.p.M_Cr) / XM_sSc
    # X_Mn_sSc = (s.p.m_Mn_sSc / s.p.M_Mn) / XM_sSc
    # X_P_sSc = (s.p.m_P_sSc / s.p.M_P) / XM_sSc
    # X_SiO2_sSc = (s.p.m_SiO2_sSc / s.p.M_SiO2) / XM_sSc
    # X_Al2O3_sSc = (s.p.m_Al2O3_sSc / s.p.M_Al2O3) / XM_sSc
    # X_CaO_sSc = (s.p.m_CaO_sSc / s.p.M_CaO) / XM_sSc
    # X_MgO_sSc = (s.p.m_MgO_sSc / s.p.M_MgO) / XM_sSc
    # X_MnO_sSc = (s.p.m_MnO_sSc / s.p.M_MnO) / XM_sSc
    # X_Si_sSc = (s.p.m_Si_sSc / s.p.M_Si) / XM_sSc
    # X_comb_sSc = (s.p.m_comb_sSc / s.p.M_C9H20) / XM_sSc
    # X_P2O5_sSc = (s.p.m_P2O5_sSc / s.p.M_P2O5) / XM_sSc

    # Mass fractions of compounds in solid metal
    MX_Fe_sSc = s.p.m_Fe_sSc / s.p.m_sSc
    MX_C_sSc = s.p.m_C_sSc / s.p.m_sSc
    MX_Cr_sSc = s.p.m_Cr_sSc / s.p.m_sSc
    MX_Mn_sSc = s.p.m_Mn_sSc / s.p.m_sSc
    MX_P_sSc = s.p.m_P_sSc / s.p.m_sSc
    MX_SiO2_sSc = s.p.m_SiO2_sSc / s.p.m_sSc
    MX_Al2O3_sSc = s.p.m_Al2O3_sSc / s.p.m_sSc
    MX_CaO_sSc = s.p.m_CaO_sSc / s.p.m_sSc
    MX_MgO_sSc = s.p.m_MgO_sSc / s.p.m_sSc
    MX_MnO_sSc = s.p.m_MnO_sSc / s.p.m_sSc
    MX_Si_sSc = s.p.m_Si_sSc / s.p.m_sSc
    MX_comb_sSc = s.p.m_comb_sSc / s.p.m_sSc
    MX_P2O5_sSc = s.p.m_P2O5_sSc / s.p.m_sSc

    # ----------- Liquid Metal ------------

    # Total mass of liquid metal [kg]
    s.p.m_lSc = (
        s.p.m_Fe_lSc
        + s.p.m_C_lSc
        + s.p.m_Cr_lSc
        + s.p.m_Mn_lSc
        + s.p.m_P_lSc
        + s.p.m_Si_lSc
    )

    # Total mole of liquid metal [mol]
    XM_lSc = (
        (s.p.m_Fe_lSc / s.p.M_Fe)
        + (s.p.m_C_lSc / s.p.M_C)
        + (s.p.m_Cr_lSc / s.p.M_Cr)
        + (s.p.m_Mn_lSc / s.p.M_Mn)
        + (s.p.m_P_lSc / s.p.M_P)
        + (s.p.m_Si_lSc / s.p.M_Si)
    )

    # Mole fractions of compounds in liquid metal
    X_Fe_lSc = (s.p.m_Fe_lSc / s.p.M_Fe) / XM_lSc
    X_C_lSc = (s.p.m_C_lSc / s.p.M_C) / XM_lSc
    X_Cr_lSc = (s.p.m_Cr_lSc / s.p.M_Cr) / XM_lSc
    X_Mn_lSc = (s.p.m_Mn_lSc / s.p.M_Mn) / XM_lSc
    X_P_lSc = (s.p.m_P_lSc / s.p.M_P) / XM_lSc
    X_Si_lSc = (s.p.m_Si_lSc / s.p.M_Si) / XM_lSc

    # Mass fractions of compounds in liquid metal
    s.p.recalc_MX_lSc()

    # ------------ Solid Slag -------------

    # Total mass of solid slag [kg]
    s.p.m_sSl = s.p.m_CaO_sSl + s.p.m_MgO_sSl + s.p.m_SiO2_sSl + s.p.m_Al2O3_sSl

    # Total mole of solid slag [mol]
    XM_sSl = (
        (s.p.m_CaO_sSl / s.p.M_CaO)
        + (s.p.m_MgO_sSl / s.p.M_MgO)
        + (s.p.m_SiO2_sSl / s.p.M_SiO2)
        + (s.p.m_Al2O3_sSl / s.p.M_Al2O3)
    )

    # Mole fractions of compounds in solid slag
    # X_CaO_sSl = (s.p.m_CaO_sSl / s.p.M_CaO) / XM_sSl
    # X_MgO_sSl = (s.p.m_MgO_sSl / s.p.M_MgO) / XM_sSl
    # X_SiO2_sSl = (s.p.m_SiO2_sSl / s.p.M_SiO2) / XM_sSl
    # X_Al2O3_sSl = (s.p.m_Al2O3_sSl / s.p.M_Al2O3) / XM_sSl

    # Mass fractions of compounds in solid slag
    MX_CaO_sSl = s.p.m_CaO_sSl / s.p.m_sSl
    MX_MgO_sSl = s.p.m_MgO_sSl / s.p.m_sSl
    MX_SiO2_sSl = s.p.m_SiO2_sSl / s.p.m_sSl
    MX_Al2O3_sSl = s.p.m_Al2O3_sSl / s.p.m_sSl

    # ----------- Liquid Slag -------------

    # Total mass of liquid slag [kg]
    s.p.m_lSl = (
        s.p.m_SiO2_lSl
        + s.p.m_Al2O3_lSl
        + s.p.m_CaO_lSl
        + s.p.m_MgO_lSl
        + s.p.m_MnO_lSl
        + s.p.m_P2O5_lSl
        + s.p.m_Cr2O3_lSl
        + s.p.m_FeO_lSl
    )

    # Total mole of liquid slag [mol]
    XM_lSl = (
        (s.p.m_SiO2_lSl / s.p.M_SiO2)
        + (s.p.m_Al2O3_lSl / s.p.M_Al2O3)
        + (s.p.m_CaO_lSl / s.p.M_CaO)
        + (s.p.m_MgO_lSl / s.p.M_MgO)
        + (s.p.m_MnO_lSl / s.p.M_MnO)
        + (s.p.m_P2O5_lSl / s.p.M_P2O5)
        + (s.p.m_Cr2O3_lSl / s.p.M_Cr2O3)
        + (s.p.m_FeO_lSl / s.p.M_FeO)
    )

    # Mole fractions of compounds in liquid slag
    X_SiO2_lSl = (s.p.m_SiO2_lSl / s.p.M_SiO2) / XM_lSl
    X_Al2O3_lSl = (s.p.m_Al2O3_lSl / s.p.M_Al2O3) / XM_lSl
    X_CaO_lSl = (s.p.m_CaO_lSl / s.p.M_CaO) / XM_lSl
    X_MgO_lSl = (s.p.m_MgO_lSl / s.p.M_MgO) / XM_lSl
    X_MnO_lSl = (s.p.m_MnO_lSl / s.p.M_MnO) / XM_lSl
    X_P2O5_lSl = (s.p.m_P2O5_lSl / s.p.M_P2O5) / XM_lSl
    X_Cr2O3_lSl = (s.p.m_Cr2O3_lSl / s.p.M_Cr2O3) / XM_lSl
    X_FeO_lSl = (s.p.m_FeO_lSl / s.p.M_FeO) / XM_lSl

    # Mass fractions of compounds in solid slag
    s.p.MX_SiO2_lSl = s.p.m_SiO2_lSl / s.p.m_lSl
    s.p.MX_Al2O3_lSl = s.p.m_Al2O3_lSl / s.p.m_lSl
    s.p.MX_CaO_lSl = s.p.m_CaO_lSl / s.p.m_lSl
    s.p.MX_MgO_lSl = s.p.m_MgO_lSl / s.p.m_lSl
    s.p.MX_MnO_lSl = s.p.m_MnO_lSl / s.p.m_lSl
    s.p.MX_P2O5_lSl = s.p.m_P2O5_lSl / s.p.m_lSl
    s.p.MX_Cr2O3_lSl = s.p.m_Cr2O3_lSl / s.p.m_lSl
    s.p.MX_FeO_lSl = s.p.m_FeO_lSl / s.p.m_lSl

    # Molar mass of liquid slag [kg/mol]
    s.p.M_lSl = (
        X_SiO2_lSl * s.p.M_SiO2
        + X_Al2O3_lSl * s.p.M_Al2O3
        + X_CaO_lSl * s.p.M_CaO
        + X_MgO_lSl * s.p.M_MgO
        + X_MnO_lSl * s.p.M_MnO
        + X_P2O5_lSl * s.p.M_P2O5
        + X_Cr2O3_lSl * s.p.M_Cr2O3
        + X_FeO_lSl * s.p.M_FeO
    )

    # --------------- Gas -----------------

    # Total mass of gas
    m_gas = s.p.m_H2O + s.p.m_CO + s.p.m_CO2 + s.p.m_O2

    # Total mole of gas
    XM_gas = (
        (s.p.m_H2O / s.p.M_H2O)
        + (s.p.m_CO / s.p.M_CO)
        + (s.p.m_CO2 / s.p.M_CO2)
        + (s.p.m_O2 / s.p.M_O2)
    )

    # Mole fraction of compounds in gas
    X_H2O = (s.p.m_H2O / s.p.M_H2O) / XM_gas
    X_CO = (s.p.m_CO / s.p.M_CO) / XM_gas
    X_CO2 = (s.p.m_CO2 / s.p.M_CO2) / XM_gas
    X_O2 = (s.p.m_O2 / s.p.M_O2) / XM_gas

    # Mass fraction of compounds in gas
    MX_H2O = s.p.m_H2O / m_gas
    MX_CO = s.p.m_CO / m_gas
    MX_CO2 = s.p.m_CO2 / m_gas
    MX_O2 = s.p.m_O2 / m_gas

    # ====================== Chemical Reactions ======================

    # ------- Injected Carbon Reaction -------

    # FeO + C -> Fe + CO
    # Decarburization reaction in mol/s
    if pt.isnan(ensure_tensor(s.p.MX_FeO_lSl)):
        r_FeO_CL = 0
    else:
        r_FeO_CL = (s.p.m_CL * s.p.kd_CL * s.p.MX_FeO_lSl) / s.p.M_C

    # ------ Dissolved C decarburization -------

    # FeO + C -> Fe + CO

    # Activity calculation
    gamma_FeO = 10 ** (
        1262 / s.p.T_lSl
        - 1.1302 * X_FeO_lSl
        + 0.96 * X_SiO2_lSl
        + 0.123 * X_CaO_lSl
        - 0.4198
    )  # Basu et al. 2008

    # Equilibrium constant
    K_FC = 10 ** (-5730 / s.p.T_lSl + 5.096)  # Turkdogan 1996

    # Partial pressure
    p_CO = s.p.p_gas * X_CO

    # Equilibrium carbon mass/ mole fraction
    k_C = p_CO / (K_FC * (gamma_FeO / (s.p.M_FeO * 1.65)))
    k_XC = k_C * ((s.p.M_lSl * s.p.M_Fe) / (s.p.M_FeO * s.p.M_C * 100**2))
    Xeq_C = ensure_tensor(
        k_XC
        * (
            (s.p.m_lSl * s.p.M_FeO) / (s.p.m_FeO_lSl * s.p.M_lSl)
            + (s.p.m_SiO2_lSl * s.p.M_FeO) / (s.p.m_FeO_lSl * s.p.M_SiO2)
            + 1
        )
    )  # Bekkar 1999
    if pt.isnan(Xeq_C):
        Xeq_C = pt.tensor(0)

    # Rate of decarburization of dissolved C
    r_FeO_CD = (s.p.kd_CD * (X_C_lSc - Xeq_C)) / s.p.M_C  # Logar 2012

    # ---------- Carbon Oxidation -----------

    # To carbon monoxide
    # C + 1/2 O2 -> CO
    r_C_hO2 = (
        s.p.kd_C1 * (X_C_lSc - Xeq_C) * s.p.O2_lance * s.p.K_O2CO
    ) / s.p.M_C  # Logar 2012
    if r_C_hO2 > (s.p.O2_lance * s.p.K_O2CO) / s.p.M_C:
        r_C_hO2 = (s.p.O2_lance * s.p.K_O2CO) / s.p.M_C

    # To carbon dioxide
    # C + O2 -> CO2
    r_C_O2 = (
        s.p.kd_C2 * (X_C_lSc - Xeq_C) * s.p.O2_lance * s.p.K_O2CO2
    ) / s.p.M_C  # Logar 2012
    if r_C_O2 > (s.p.O2_lance * s.p.K_O2CO2) / s.p.M_C:
        r_C_O2 = (s.p.O2_lance * s.p.K_O2CO2) / s.p.M_C

    # -------- MnO decarburization ----------

    # MnO + C -> Mn + CO

    # Equilibrium constant
    kX_Mn1 = 6.4 * p_CO * X_MnO_lSl

    # Equilibrium mole fraction
    Xeq_MnO1 = ensure_tensor(X_Mn_lSc / kX_Mn1)  # Logar 2012

    if pt.isnan(Xeq_MnO1):
        Xeq_MnO1 = 0

    # Rate of reaction
    r_MnO_C = (s.p.kd_Mn1 * (X_MnO_lSl - Xeq_MnO1)) / s.p.M_MnO

    # ----------- Desiliconization ----------

    # 2FeO + Si -> 2Fe + SiO2

    # Basicity
    B3 = (s.p.MX_CaO_lSl * s.p.MX_MgO_lSl) / (s.p.MX_SiO2_lSl * s.p.MX_Al2O3_lSl)

    # Activity of SiO2 based on basicity
    a_SiO2_bas = pt.exp(
        ensure_tensor((6728 / s.p.T_lSl) - (0.920 * B3 + 6.994))
    )  # Meraikib 1995

    # Equilibrium constant
    K_Si = 10 ** (30410 / s.p.T_lSc - 11.59)  # Turkdogan 1996

    # Oxygen Solubility
    O_sol = 10 ** (-6380 / s.p.T_lSc + 2.765)  # Turkdogan 1996

    # Equilibrium fraction
    MXeq_Si = a_SiO2_bas / (K_Si * O_sol**2)  # Turkogan 1996
    Xeq_Si = ensure_tensor(MXeq_Si * (s.p.M_Fe / (s.p.M_Si * 100)))

    if pt.isnan(Xeq_Si):
        Xeq_Si = 0

    # Rate of reaction
    r_2FeO_Si = (s.p.kd_Si1 * (X_Si_lSc - Xeq_Si)) / s.p.M_Si

    # --------- Silicon Oxidation ---------

    # Si + O2 -> SiO2

    r_Si_O2 = (
        s.p.kd_Si2 * (X_Si_lSc - Xeq_Si) * s.p.O2_lance * s.p.K_O2SiO2
    ) / s.p.M_Si
    if r_Si_O2 > (s.p.O2_lance * s.p.K_O2SiO2) / s.p.M_Si:
        r_Si_O2 = (s.p.O2_lance * s.p.K_O2SiO2) / s.p.M_Si

    # ------- Si reaction with MnO --------

    # 2MnO + Si -> 2Mn + SiO2

    # Reaction equilibrium constant
    kX_Mn2 = 10 ** (2.8 * B3 - 1.16) * (
        (s.p.M_MnO**2 * s.p.M_Si * s.p.M_Fe) / (s.p.M_Mn**2 * s.p.M_lSl * s.p.M_SiO2)
    )  # Logar 2012

    # Equilibrium MnO mole fraction
    Xeq_MnO2 = pt.sqrt(
        ensure_tensor((X_Mn_lSc**2 * X_SiO2_lSl) / (X_Si_lSc * kX_Mn2))
    )  # Logar 2012

    if pt.isnan(ensure_tensor(Xeq_MnO2)):
        Xeq_MnO2 = 0

    # Rate of reaction
    r_2MnO_Si = (s.p.kd_Mn2 * (X_MnO_lSl - Xeq_MnO2)) / s.p.M_MnO

    # -------- Mn reaction with FeO --------

    # Mn + FeO -> MnO + Fe

    # Equilibrium constant
    K_FeMn = 1.8  # Turkdogan 1996 (Given that B = 2.5-4.0 and 1600 - 1650 C)
    kX_Mn = K_FeMn * (s.p.M_FeO * s.p.M_Mn * 100) / (s.p.M_MnO * s.p.M_Fe)

    # Equilibrium fraction
    Xeq_Mn = ensure_tensor(X_MnO_lSl / (X_FeO_lSl * kX_Mn))

    if pt.isnan(Xeq_Mn):
        Xeq_Mn = 0

    # Rate of reaction
    r_FeO_Mn = (s.p.kd_Mn * (X_Mn_lSc - Xeq_Mn)) / s.p.M_Mn

    # ------- Cr reaction with FeO ---------

    # 3FeO + 2Cr -> 3Fe + Cr2O3

    # Equilibrium constants
    K_FeCr = 0.3  # Trukdogan
    kX_Cr = K_FeCr * (s.p.M_Cr * s.p.M_FeO * 100) / (s.p.M_Cr2O3 * s.p.M_Fe)

    # Equilibrium mole fraction
    Xeq_Cr = ensure_tensor(X_Cr2O3_lSl / (X_FeO_lSl * kX_Cr))

    if pt.isnan(Xeq_Cr):
        Xeq_Cr = 0

    # Rate of reaction
    r_3FeO_2Cr = (2 * s.p.kd_Cr1 * (X_Cr_lSc - Xeq_Cr)) / s.p.M_Cr

    # --------- Chromium Oxidation ---------

    # 2Cr + 3/2O2 -> Cr2O3

    r_2Cr_3hO2 = (
        2 * s.p.kd_Cr2 * (X_Cr_lSc - Xeq_Cr) * s.p.O2_lance * s.p.K_O2Cr2O3
    ) / s.p.M_Cr
    if r_2Cr_3hO2 > (s.p.O2_lance * s.p.K_O2Cr2O3) / s.p.M_Cr:
        r_2Cr_3hO2 = (s.p.O2_lance * s.p.K_O2Cr2O3) / s.p.M_Cr

    # ----- Phosphorus reaction with FeO -----

    # 5FeO + 2P -> 5Fe + P2O5

    partition = 10 ** (
        1.97 * X_CaO_lSl + 2.0 * X_FeO_lSl - 2.04 * X_SiO2_lSl + 6713 / s.p.T_lSl - 1.84
    )  # Basu, 2007
    eq_P = (2 * (s.p.m_P2O5_lSl / s.p.M_P2O5) * s.p.M_P) / partition
    Xeq_P = ensure_tensor(eq_P / XM_lSc)

    if pt.isnan(Xeq_P):
        Xeq_P = 0

    r_5FeO_2P = (2 * s.p.kd_P * (X_P_lSc - Xeq_P)) / s.p.M_P

    # ------------- Fe Oxidation -------------

    # Fe + 1/2O2 -> FeO

    r_Fe_hO2 = (s.p.O2_lance * s.p.K_O2FeO) / s.p.M_Fe

    # ------------- Combustion ---------------

    # C9H20 + 14O2 -> 9CO2 + 10H2O

    r_comb = (s.p.kd_comb * s.p.m_comb_sSc * (s.p.T_sSc / s.p.T_melt)) / s.p.M_C9H20

    # No reaction if no O2 avilable:
    if r_comb > (s.p.m_O2 / s.p.M_O2):
        r_comb = 0

    # ----------- Post Combustion ------------

    # CO + 1/2O2 -> CO2

    K_mCO = 0.9

    r_post = (s.p.O2_post * K_mCO) / s.p.M_O2

    # --------- Electrode Oxidation ----------

    # C + O2 -> CO2

    dm_el = 3 * (
        (s.p.R_tip * (s.p.I_arc**2 / 3600)) + (s.p.R_side * (s.p.A_side / 3600))
    )

    # No reaction if no O2 avilable:
    if dm_el > s.p.m_O2:
        dm_el = 0

    # =================== Reaction Heat Transfer ====================

    # ------------ Dynamic heat capacity calculation ----------
    # Units in kJ/mol K

    if s.p.T_gas < 500:
        t_H2O = (s.p.T_gas - 298) / 1000
        CpdT_H2O = (
            -203.6060 * t_H2O
            + (1523.290 / 2) * (t_H2O**2)
            + (-3196.413 / 3) * (t_H2O**3)
            + (2474.455 / 4) * (t_H2O**4)
            - (3.855326) / t_H2O
        )
    elif (500 <= s.p.T_gas) and (s.p.T_gas < 1700):
        t_H2O = (500 - 298) / 1000
        CpdT_H2O1 = (
            -203.6060 * t_H2O
            + (1523.290 / 2) * (t_H2O**2)
            + (-3196.413 / 3) * (t_H2O**3)
            + (2474.455 / 4) * (t_H2O**4)
            - (3.855326) / t_H2O
        )
        t_H2O_2 = (s.p.T_gas - 298) / 1000
        CpdT_H2O2 = (
            30.0920 * t_H2O_2
            + (6.832514 / 2) * (t_H2O_2**2)
            + (6.793435 / 3) * (t_H2O_2**3)
            + (-2.534480 / 4) * (t_H2O_2**4)
            - (0.082139) / t_H2O_2
        )
        CpdT_H2O = CpdT_H2O1 + CpdT_H2O2
    else:
        t_H2O = (500 - 298) / 1000
        #         CpdT_H2O1 = -203.6060*t_H2O + (1523.290/2)*(t_H2O**2) + (-3196.413/3)*(t_H2O**3) \
        #         + (2474.455/4)*(t_H2O**4) - (3.855326)/t_H2O
        CpdT_H2O1 = 79 * t_H2O
        t_H2O_2 = (1700 - 500) / 1000
        CpdT_H2O2 = (
            30.0920 * t_H2O_2
            + (6.832514 / 2) * (t_H2O_2**2)
            + (6.793435 / 3) * (t_H2O_2**3)
            + (-2.534480 / 4) * (t_H2O_2**4)
            - (0.082139) / t_H2O_2
        )
        t_H2O_3 = (s.p.T_gas - 1700) / 1000
        #         CpdT_H2O3 = 41.96426*t_H2O_3 + (8.622053/2)*(t_H2O_3**2) + (-1.499780/3)*(t_H2O_3**3) \
        #         + (0.098119/4)*(t_H2O_3**4) - (-11.15764)/t_H2O_3
        CpdT_H2O3 = 49.75 * t_H2O_3
        CpdT_H2O = CpdT_H2O1 + CpdT_H2O2 + CpdT_H2O3

    t_C = (s.p.T_lSc - 298) / 1000
    CpdT_C = (
        21.17510 * t_C
        + (-0.812428 / 2) * (t_C**2)
        + (0.448537 / 3) * (t_C**3)
        + (-0.043256 / 4) * (t_C**4)
        - (-0.013103) / t_C
    )

    t_C_gas = (s.p.T_gas - 298) / 1000
    CpdT_C_gas = (
        21.17510 * t_C_gas
        + (-0.812428 / 2) * (t_C_gas**2)
        + (0.448537 / 3) * (t_C_gas**3)
        + (-0.043256 / 4) * (t_C_gas**4)
        - (-0.013103) / t_C_gas
    )

    if s.p.T_lSc < 1650:
        t_FeO = (s.p.T_lSc - 298) / 1000
        CpdT_FeO = (
            45.75120 * t_FeO
            + (18.78553 / 2) * (t_FeO**2)
            + (-5.952201 / 3) * (t_FeO**3)
            + (0.852779 / 4) * (t_FeO**4)
            - (-0.081265) / t_FeO
        )
    else:
        t_FeO = (1650 - 298) / 1000
        CpdT_FeO1 = (
            45.75120 * t_FeO
            + (18.78553 / 2) * (t_FeO**2)
            + (-5.952201 / 3) * (t_FeO**3)
            + (0.852779 / 4) * (t_FeO**4)
            - (-0.081265) / t_FeO
        )
        t_FeO_2 = (s.p.T_lSc - 1650) / 1000
        CpdT_FeO2 = 68.1992 * t_FeO_2
        CpdT_FeO = CpdT_FeO1 + CpdT_FeO2

    t_Fe = (s.p.T_lSc - 298) / 1000
    CpdT_Fe = (
        23.97449 * t_Fe
        + (8.367750 / 2) * (t_Fe**2)
        + (0.000277 / 3) * (t_Fe**3)
        + (-0.000086 / 4) * (t_Fe**4)
        - (-0.000005) / t_Fe
    )

    if s.p.T_gas < 700:
        t_O2_gas = (s.p.T_gas - 298) / 1000
        CpdT_O2_gas = (
            31.32234 * t_O2_gas
            + (-20.23532 / 2) * (t_O2_gas**2)
            + (57.86644 / 3) * (t_O2_gas**3)
            + (-36.50624 / 4) * (t_O2_gas**4)
            - (-0.007374) / t_O2_gas
        )
    else:
        t_O2_gas = (700 - 298) / 1000
        CpdT_O2_gas1 = (
            31.32234 * t_O2_gas
            + (-20.23532 / 2) * (t_O2_gas**2)
            + (57.86644 / 3) * (t_O2_gas**3)
            + (-36.50624 / 4) * (t_O2_gas**4)
            - (-0.007374) / t_O2_gas
        )
        t_O2_gas2 = (s.p.T_gas - 700) / 1000
        CpdT_O2_gas2 = (
            30.03235 * t_O2_gas2
            + (8.772972 / 2) * (t_O2_gas2**2)
            + (-3.988133 / 3) * (t_O2_gas2**3)
            + (0.788313 / 4) * (t_O2_gas2**4)
            - (-0.741599) / t_O2_gas2
        )
        CpdT_O2_gas = CpdT_O2_gas1 + CpdT_O2_gas2

    if s.p.T_lSc < 700:
        t_O2_lSc = (s.p.T_lSc - 298) / 1000
        CpdT_O2_lSc = (
            31.32234 * t_O2_lSc
            + (-20.23532 / 2) * (t_O2_lSc**2)
            + (57.86644 / 3) * (t_O2_lSc**3)
            + (-36.50624 / 4) * (t_O2_lSc**4)
            - (-0.007374) / t_O2_lSc
        )
    else:
        t_O2_lSc1 = (700 - 298) / 1000
        CpdT_O2_lSc1 = (
            31.32234 * t_O2_lSc1
            + (-20.23532 / 2) * (t_O2_lSc1**2)
            + (57.86644 / 3) * (t_O2_lSc1**3)
            + (-36.50624 / 4) * (t_O2_lSc1**4)
            - (-0.007374) / t_O2_lSc1
        )
        t_O2_lSc2 = (s.p.T_lSc - 700) / 1000
        CpdT_O2_lSc2 = (
            30.03235 * t_O2_lSc2
            + (8.772972 / 2) * (t_O2_lSc2**2)
            + (-3.988133 / 3) * (t_O2_lSc2**3)
            + (0.788313 / 4) * (t_O2_lSc2**4)
            - (-0.741599) / t_O2_lSc2
        )
        CpdT_O2_lSc = CpdT_O2_lSc1 + CpdT_O2_lSc2

    if s.p.T_gas < 1300:
        t_CO_gas = (s.p.T_gas - 298) / 1000
        CpdT_CO_gas = (
            25.56759 * t_CO_gas
            + (6.096130 / 2) * (t_CO_gas**2)
            + (4.054656 / 3) * (t_CO_gas**3)
            + (-2.671301 / 4) * (t_CO_gas**4)
            - (0.131021) / t_CO_gas
        )
    else:
        t_CO_gas = (1300 - 298) / 1000
        CpdT_CO_gas_1 = (
            25.56759 * t_CO_gas
            + (6.096130 / 2) * (t_CO_gas**2)
            + (4.054656 / 3) * (t_CO_gas**3)
            + (-2.671301 / 4) * (t_CO_gas**4)
            - (0.131021) / t_CO_gas
        )
        t_CO_gas_2 = (s.p.T_gas - 1300) / 1000
        CpdT_CO_gas_2 = (
            35.15070 * t_CO_gas_2
            + (1.300095 / 2) * (t_CO_gas_2**2)
            + (-0.205921 / 3) * (t_CO_gas_2**3)
            + (0.013550 / 4) * (t_CO_gas_2**4)
            - (-3.282780) / t_CO_gas_2
        )
        CpdT_CO_gas = CpdT_CO_gas_1 + CpdT_CO_gas_2

    if s.p.T_lSc < 1300:
        t_CO_lSc = (s.p.T_gas - 298) / 1000
        CpdT_CO_lSc = (
            25.56759 * t_CO_lSc
            + (6.096130 / 2) * (t_CO_lSc**2)
            + (4.054656 / 3) * (t_CO_lSc**3)
            + (-2.671301 / 4) * (t_CO_lSc**4)
            - (0.131021) / t_CO_lSc
        )
    else:
        t_CO_lSc = (1300 - 298) / 1000
        CpdT_CO_lSc_1 = (
            25.56759 * t_CO_lSc
            + (6.096130 / 2) * (t_CO_lSc**2)
            + (4.054656 / 3) * (t_CO_lSc**3)
            + (-2.671301 / 4) * (t_CO_lSc**4)
            - (0.131021) / t_CO_lSc
        )
        t_CO_lSc_2 = (s.p.T_lSc - 1300) / 1000
        CpdT_CO_lSc_2 = (
            35.15070 * t_CO_lSc_2
            + (1.300095 / 2) * (t_CO_lSc_2**2)
            + (-0.205921 / 3) * (t_CO_lSc_2**3)
            + (0.013550 / 4) * (t_CO_lSc_2**4)
            - (-3.282780) / t_CO_lSc_2
        )
        CpdT_CO_lSc = CpdT_CO_lSc_1 + CpdT_CO_lSc_2

    CpdT_MnO = 0.04869 * (s.p.T_lSc - 298)

    if s.p.T_lSc < 980:
        t_Mn = (s.p.T_lSc - 298) / 1000
        CpdT_Mn = (
            27.24190 * t_Mn
            + (5.237640 / 2) * (t_Mn**2)
            + (7.783160 / 3) * (t_Mn**3)
            + (-2.118501 / 4) * (t_Mn**4)
            - (-0.282113) / t_Mn
        )
    elif (980 <= s.p.T_lSc) and (s.p.T_lSc < 1361):
        t_Mn = (980 - 298) / 1000
        CpdT_Mn_1 = (
            27.24190 * t_Mn
            + (5.237640 / 2) * (t_Mn**2)
            + (7.783160 / 3) * (t_Mn**3)
            + (-2.118501 / 4) * (t_Mn**4)
            - (-0.282113) / t_Mn
        )
        t_Mn2 = (s.p.T_lSc - 980) / 1000
        CpdT_Mn_2 = (
            52.29870 * t_Mn2
            + (-28.67560 / 2) * (t_Mn2**2)
            + (21.48670 / 3) * (t_Mn2**3)
            + (-4.979850 / 4) * (t_Mn2**4)
            - (-2.432060) / t_Mn2
        )
        CpdT_Mn = CpdT_Mn_1 + CpdT_Mn_2
    elif (1361 <= s.p.T_lSc) and (s.p.T_lSc < 1412):
        t_Mn = (980 - 298) / 1000
        CpdT_Mn_1 = (
            27.24190 * t_Mn
            + (5.237640 / 2) * (t_Mn**2)
            + (7.783160 / 3) * (t_Mn**3)
            + (-2.118501 / 4) * (t_Mn**4)
            - (-0.282113) / t_Mn
        )
        t_Mn2 = (1361 - 980) / 1000
        CpdT_Mn_2 = (
            52.29870 * t_Mn2
            + (-28.67560 / 2) * (t_Mn2**2)
            + (21.48670 / 3) * (t_Mn2**3)
            + (-4.979850 / 4) * (t_Mn2**4)
            - (-2.432060) / t_Mn2
        )
        t_Mn3 = (1412 - 1361) / 1000
        #         CpdT_Mn_3 = 19.06450*t_Mn3 + (31.41340/2)*(t_Mn3**2) + (-14.99350/3)*(t_Mn3**3) \
        #         + (3.214741/4)*(t_Mn3**4) - (1.867090)/t_Mn3
        CpdT_Mn_3 = 43.3 * t_Mn3
        CpdT_Mn = CpdT_Mn_1 + CpdT_Mn_2 + CpdT_Mn_3
    elif (1412 <= s.p.T_lSc) and (s.p.T_lSc < 1519):
        t_Mn = (980 - 298) / 1000
        CpdT_Mn_1 = (
            27.24190 * t_Mn
            + (5.237640 / 2) * (t_Mn**2)
            + (7.783160 / 3) * (t_Mn**3)
            + (-2.118501 / 4) * (t_Mn**4)
            - (-0.282113) / t_Mn
        )
        t_Mn2 = (1361 - 980) / 1000
        CpdT_Mn_2 = (
            52.29870 * t_Mn2
            + (-28.67560 / 2) * (t_Mn2**2)
            + (21.48670 / 3) * (t_Mn2**3)
            + (-4.979850 / 4) * (t_Mn2**4)
            - (-2.432060) / t_Mn2
        )
        t_Mn3 = (1412 - 1361) / 1000
        #         CpdT_Mn_3 = 19.06450*t_Mn3 + (31.41340/2)*(t_Mn3**2) + (-14.99350/3)*(t_Mn3**3) \
        #         + (3.214741/4)*(t_Mn3**4) - (1.867090)/t_Mn3
        CpdT_Mn_3 = 43.3 * t_Mn3
        t_Mn4 = (1519 - 1412) / 1000
        #         CpdT_Mn_4 = -534.1720*t_Mn4 + (679.0530/2)*(t_Mn4**2) + (-296.3700/3)*(t_Mn4**3) \
        #         + (46.42660/4)*(t_Mn4**4) - (161.3420)/t_Mn4
        CpdT_Mn_4 = 45.8 * t_Mn4
        CpdT_Mn = CpdT_Mn_1 + CpdT_Mn_2 + CpdT_Mn_3 + CpdT_Mn_4
    else:
        t_Mn = (980 - 298) / 1000
        CpdT_Mn_1 = (
            27.24190 * t_Mn
            + (5.237640 / 2) * (t_Mn**2)
            + (7.783160 / 3) * (t_Mn**3)
            + (-2.118501 / 4) * (t_Mn**4)
            - (-0.282113) / t_Mn
        )
        t_Mn2 = (1361 - 980) / 1000
        CpdT_Mn_2 = (
            52.29870 * t_Mn2
            + (-28.67560 / 2) * (t_Mn2**2)
            + (21.48670 / 3) * (t_Mn2**3)
            + (-4.979850 / 4) * (t_Mn2**4)
            - (-2.432060) / t_Mn2
        )
        t_Mn3 = (1412 - 1361) / 1000
        #         CpdT_Mn_3 = 19.06450*t_Mn3 + (31.41340/2)*(t_Mn3**2) + (-14.99350/3)*(t_Mn3**3) \
        #         + (3.214741/4)*(t_Mn3**4) - (1.867090)/t_Mn3
        CpdT_Mn_3 = 43.3 * t_Mn3
        t_Mn4 = (1519 - 1412) / 1000
        #         CpdT_Mn_4 = -534.1720*t_Mn4 + (679.0530/2)*(t_Mn4**2) + (-296.3700/3)*(t_Mn4**3) \
        #         + (46.42660/4)*(t_Mn4**4) - (161.3420)/t_Mn4
        CpdT_Mn_4 = 45.8 * t_Mn4
        t_Mn5 = (s.p.T_lSc - 1519) / 1000
        CpdT_Mn_5 = (
            46.02400 * t_Mn5
            + ((1.953485e-7) / 2) * (t_Mn5**2)
            + ((-7.567225e-8) / 3) * (t_Mn5**3)
            + ((1.005938e-8) / 4) * (t_Mn4**5)
            - (5.623757e-8) / t_Mn5
        )
        CpdT_Mn = CpdT_Mn_1 + CpdT_Mn_2 + CpdT_Mn_3 + CpdT_Mn_4 + CpdT_Mn_5

    if s.p.T_lSc < 847:
        t_SiO2 = (s.p.T_lSc - 298) / 1000
        CpdT_SiO2 = (
            -6.076591 * t_SiO2
            + (251.6755 / 2) * (t_SiO2**2)
            + (-324.7964 / 3) * (t_SiO2**3)
            + (168.5604 / 4) * (t_SiO2**4)
            - (0.002548) / t_SiO2
        )
    else:
        t_SiO2 = (847 - 298) / 1000
        CpdT_SiO2_1 = (
            -6.076591 * t_SiO2
            + (251.6755 / 2) * (t_SiO2**2)
            + (-324.7964 / 3) * (t_SiO2**3)
            + (168.5604 / 4) * (t_SiO2**4)
            - (0.002548) / t_SiO2
        )
        t_SiO2_2 = (s.p.T_lSc - 847) / 1000
        CpdT_SiO2_2 = (
            58.75340 * t_SiO2_2
            + (10.27925 / 2) * (t_SiO2_2**2)
            + (-0.131384 / 3) * (t_SiO2_2**3)
            + (0.025210 / 4) * (t_SiO2_2**4)
            - (0.025601) / t_SiO2_2
        )
        CpdT_SiO2 = CpdT_SiO2_1 + CpdT_SiO2_2

    if s.p.T_lSc < 1685:
        t_Si = (s.p.T_lSc - 298) / 1000
        CpdT_Si = (
            22.81719 * (t_Si)
            + (3.899510 / 2) * (t_Si**2)
            + (-0.082885 / 3) * (t_Si**3)
            + (0.042111 / 4) * (t_Si**4)
            - (-0.354063) / t_Si
        )
    else:
        t_Si = (1685 - 298) / 1000
        CpdT_Si_1 = (
            22.81719 * (t_Si)
            + (3.899510 / 2) * (t_Si**2)
            + (-0.082885 / 3) * (t_Si**3)
            + (0.042111 / 4) * (t_Si**4)
            - (-0.354063) / t_Si
        )
        t_Si_2 = (s.p.T_lSc - 1685) / 1000
        CpdT_Si_2 = 27.19604 * (t_Si_2)
        CpdT_Si = CpdT_Si_1 + CpdT_Si_2

    t_Cr2O3 = (s.p.T_lSc - 298) / 1000
    CpdT_Cr2O3 = (
        124.6550 * t_Cr2O3
        + (-0.337045 / 2) * (t_Cr2O3**2)
        + (5.705010 / 3) * (t_Cr2O3**3)
        + (-1.053470 / 4) * (t_Cr2O3**4)
        - (-2.030501) / t_Cr2O3
    )

    if s.p.T_lSc < 600:
        t_Cr = (s.p.T_lSc - 298) / 1000
        CpdT_Cr = (
            7.489737 * t_Cr
            + (71.50498 / 2) * (t_Cr**2)
            + (-91.67562 / 3) * (t_Cr**3)
            + (46.04450 / 4) * (t_Cr**4)
            - (0.138157) / t_Cr
        )
    else:
        t_Cr = (600 - 298) / 1000
        CpdT_Cr_1 = (
            7.489737 * t_Cr
            + (71.50498 / 2) * (t_Cr**2)
            + (-91.67562 / 3) * (t_Cr**3)
            + (46.04450 / 4) * (t_Cr**4)
            - (0.138157) / t_Cr
        )
        t_Cr2 = (s.p.T_lSc - 600) / 1000
        CpdT_Cr_2 = (
            18.46508 * t_Cr2
            + (5.477986 / 2) * (t_Cr2**2)
            + (7.904329 / 3) * (t_Cr2**3)
            + (-1.147848 / 4) * (t_Cr2**4)
            - (1.265791) / t_Cr2
        )
        CpdT_Cr = CpdT_Cr_1 + CpdT_Cr_2

    CpdT_P2O5 = 0.143 * (s.p.T_lSc - 298)

    if s.p.T_lSc < 1180:
        CpdT_P = 0.02633 * (s.p.T_lSc - 298)
    else:
        CpdT_P_1 = 0.02633 * (1180 - 298)
        t_P = (s.p.T_lSc - 1180) / 1000
        CpdT_P_2 = (
            20.44403 * t_P
            + (1.051745 / 2) * (t_P**2)
            + (-1.098514 / 3) * (t_P**3)
            + (0.377924 / 4) * (t_P**4)
            - (0.010645) / t_P
        )
        CpdT_P = CpdT_P_1 + CpdT_P_2

    if s.p.T_gas < 1200:
        t_CO2_gas = (s.p.T_gas - 298) / 1000
        CpdT_CO2_gas = (
            24.99735 * t_CO2_gas
            + (55.18696 / 2) * (t_CO2_gas**2)
            + (-33.69137 / 3) * (t_CO2_gas**3)
            + (7.948387 / 4) * (t_CO2_gas**4)
            - (-0.136638) / t_CO2_gas
        )
    else:
        t_CO2_gas = (1200 - 298) / 1000
        CpdT_CO2_gas_1 = (
            24.99735 * t_CO2_gas
            + (55.18696 / 2) * (t_CO2_gas**2)
            + (-33.69137 / 3) * (t_CO2_gas**3)
            + (7.948387 / 4) * (t_CO2_gas**4)
            - (-0.136638) / t_CO2_gas
        )
        t_CO2_gas_2 = (s.p.T_gas - 1200) / 1000
        CpdT_CO2_gas_2 = (
            58.16639 * t_CO2_gas_2
            + (2.720074 / 2) * (t_CO2_gas_2**2)
            + (-0.492289 / 3) * (t_CO2_gas_2**3)
            + (0.038844 / 4) * (t_CO2_gas_2**4)
            - (-6.447293) / t_CO2_gas_2
        )
        CpdT_CO2_gas = CpdT_CO2_gas_1 + CpdT_CO2_gas_2

    if s.p.T_lSc < 1200:
        t_CO2_lSc = (s.p.T_lSc - 298) / 1000
        CpdT_CO2_lSc = (
            24.99735 * t_CO2_lSc
            + (55.18696 / 2) * (t_CO2_lSc**2)
            + (-33.69137 / 3) * (t_CO2_lSc**3)
            + (7.948387 / 4) * (t_CO2_lSc**4)
            - (-0.136638) / t_CO2_lSc
        )
    else:
        t_CO2_lSc = (1200 - 298) / 1000
        CpdT_CO2_lSc_1 = (
            24.99735 * t_CO2_lSc
            + (55.18696 / 2) * (t_CO2_lSc**2)
            + (-33.69137 / 3) * (t_CO2_lSc**3)
            + (7.948387 / 4) * (t_CO2_lSc**4)
            - (-0.136638) / t_CO2_lSc
        )
        t_CO2_lSc_2 = (s.p.T_lSc - 1200) / 1000
        CpdT_CO2_lSc_2 = (
            58.16639 * t_CO2_lSc_2
            + (2.720074 / 2) * (t_CO2_lSc_2**2)
            + (-0.492289 / 3) * (t_CO2_lSc_2**3)
            + (0.038844 / 4) * (t_CO2_lSc_2**4)
            - (-6.447293) / t_CO2_lSc_2
        )
        CpdT_CO2_lSc = CpdT_CO2_lSc_1 + CpdT_CO2_lSc_2

    Cp_CH4 = 0.0586
    CpdT_C9H20 = 0.40334 * (s.p.T_gas - 298)

    # ----------------- Heat of reaction -----------------

    # a) Fe + 1/2O2 -> FeO
    dH_Ta = r_Fe_hO2 * (
        s.p.dH_FeO + s.p.dH_FeS + CpdT_FeO - CpdT_Fe - 0.5 * CpdT_O2_lSc
    )

    # b) FeO + C -> Fe + CO
    dH_Tb = (r_FeO_CL + r_FeO_CD) * (
        s.p.dH_CO - s.p.dH_CS - s.p.dH_FeO + CpdT_Fe + CpdT_CO_lSc - CpdT_C - CpdT_FeO
    )

    # c) FeO + Mn -> Fe + MnO
    dH_Tc = r_FeO_Mn * (
        s.p.dH_MnO - s.p.dH_FeO - s.p.dH_MnS + CpdT_Fe + CpdT_MnO - CpdT_FeO - CpdT_Mn
    )

    # d) 2FeO + Si -> 2Fe + SiO2
    dH_Td = r_2FeO_Si * (
        (s.p.dH_SiO2 + s.p.dH_SiO2S - 2 * s.p.dH_FeO - s.p.dH_SiS)
        + (2 * CpdT_Fe + CpdT_SiO2 - 2 * CpdT_FeO - CpdT_Si)
    )

    # e) 3FeO + 2Cr -> 3Fe + Cr2O3
    dH_Te = r_3FeO_2Cr * (
        s.p.dH_Cr2O3
        - 3 * s.p.dH_FeO
        - 2 * s.p.dH_CrS
        + 3 * CpdT_Fe
        + CpdT_Cr2O3
        - 3 * CpdT_FeO
        - 2 * CpdT_Cr
    )

    # f) 5FeO + 2P -> 5Fe + P2O5
    dH_Tf = r_5FeO_2P * (
        s.p.dH_P2O5
        - 5 * s.p.dH_FeO
        - 2 * s.p.dH_PS
        + 5 * CpdT_Fe
        + CpdT_P2O5
        - 5 * CpdT_FeO
        - 2 * CpdT_P
    )

    # g) C + 1/2O2 -> CO
    dH_Tg = r_C_hO2 * (
        (s.p.dH_CO - s.p.dH_CS) + CpdT_CO_lSc - CpdT_C - 0.5 * CpdT_O2_lSc
    )

    # h) CO + 1/2O2 -> CO2
    dH_Th = r_post * (
        (s.p.dH_CO2 - s.p.dH_CO) + CpdT_CO2_gas - CpdT_CO_gas - 0.5 * CpdT_O2_gas
    )

    # i) C + O2 -> CO2
    dH_Ti = r_C_O2 * ((s.p.dH_CO2 - s.p.dH_CS) + CpdT_CO2_lSc - CpdT_C - CpdT_O2_lSc)

    # j) MnO + C -> Mn + CO
    dH_Tj = r_MnO_C * (
        (s.p.dH_CO + s.p.dH_MnS - s.p.dH_MnO - s.p.dH_CS)
        + CpdT_Mn
        + CpdT_CO_lSc
        - CpdT_MnO
        - CpdT_C
    )

    # k) 2MnO + Si -> 2Mn + SiO2
    dH_Tk = r_2MnO_Si * (
        (s.p.dH_SiO2 + s.p.dH_SiO2S + 2 * s.p.dH_MnS - 2 * s.p.dH_MnO - s.p.dH_SiS)
        + 2 * CpdT_Mn
        + CpdT_SiO2
        - CpdT_Si
        - 2 * CpdT_MnO
    )

    # l) Si + O2 -> SiO2
    dH_Tl = r_Si_O2 * (
        (s.p.dH_SiO2 + s.p.dH_SiO2S - s.p.dH_SiS) + CpdT_SiO2 - CpdT_Si - CpdT_O2_lSc
    )

    # m) 2Cr + 3/2O2 -> Cr2O3
    dH_Tm = r_2Cr_3hO2 * (
        (s.p.dH_Cr2O3 - 2 * s.p.dH_CrS) + CpdT_Cr2O3 - 2 * CpdT_Cr - 1.5 * CpdT_O2_lSc
    )

    # Original n) removed now n) = paper's p)

    # n) C9H20 + 14O2 -> 9CO2 + 10H2O
    dH_Tn = r_comb * (
        (9 * s.p.dH_CO2 + 10 * s.p.dH_H2O - s.p.dH_C9H20)
        + 9 * CpdT_CO2_gas
        + 10 * CpdT_H2O
        - CpdT_C9H20
        - 14 * CpdT_O2_gas
    )

    # o) Graphite to CO2
    dH_To = (dm_el / s.p.M_C) * (s.p.dH_CO2 + CpdT_CO2_gas - CpdT_C_gas - CpdT_O2_gas)

    # ======================== Heat Transfer (kW) =========================

    # --------------- Solid Metal ---------------

    # Energy dissipated from the arcs by conduction
    Q_arc = 0.2 * s.p.P_arc

    # Conduction between the solid and liquid metal zones
    Q_lScsSc = (
        pt.min(ensure_tensor([s.p.m_lSc, s.p.m_sSc]))
        * s.p.K_therm1
        * s.p.K_area1
        * (s.p.T_lSc - s.p.T_sSc)
    )

    # Conduction between solid metal and solid slag
    Q_sScsSl = (
        pt.min(ensure_tensor([s.p.m_sSc, s.p.m_sSl]))
        * s.p.K_therm2
        * s.p.K_area2
        * (s.p.T_sSc - s.p.T_sSl)
    )

    # Conduction between solid metal and liquid slag
    Q_sSclSl = (
        pt.min(ensure_tensor([s.p.m_sSc, s.p.m_lSl]))
        * s.p.K_therm3
        * s.p.K_area3
        * (s.p.T_sSc - s.p.T_lSl)
    )

    # Convection between solid metal and gas zone
    Q_sScgas = (
        (s.p.m_sSc / s.p.m_EAF)
        * s.p.K_therm4
        * (s.p.T_sSc - s.p.T_gas)
        * (1 - s.p.K_sSclSc)
    )

    # Cooling of solid metal to the wall
    Q_sScwater = (
        s.p.K_water1
        * (s.p.T_sSc - s.p.T_wall)
        * (s.p.T_sSc / s.p.T_melt)
        * (1 - pt.exp(ensure_tensor(-(s.p.m_sSc / s.p.m_EAF))))
    )

    # --------------- Liquid Metal ---------------

    # Conduction between liquid metal and solid slag
    Q_lScsSl = (
        pt.min(ensure_tensor([s.p.m_lSc, s.p.m_sSl]))
        * s.p.K_therm5
        * s.p.K_area5
        * (s.p.T_lSc - s.p.T_sSl)
    )

    # Conduction between liquid metal and liquid slag
    Q_lSclSl = (
        pt.min(ensure_tensor([s.p.m_lSc, s.p.m_lSl]))
        * s.p.K_therm6
        * s.p.K_area6
        * (s.p.T_lSc - s.p.T_lSl)
    )

    # Convection between the liquid metal and surrounding gas
    Q_lScgas = (
        (s.p.m_lSc / s.p.m_EAF) * s.p.K_therm7 * (s.p.T_lSc - s.p.T_gas) * s.p.K_sSclSc
    )

    # Cooling of liquid metal to furnace wall
    Q_lScwater = (
        s.p.K_water2
        * (s.p.T_lSc - s.p.T_wall)
        * (s.p.T_lSc / s.p.T_melt)
        * (1 - pt.exp(ensure_tensor(-(s.p.m_lSc / s.p.m_EAF))))
    )

    # --------------- Solid Slag ---------------

    # Cooling of solid slag to furnace wall
    Q_sSlwater = (
        s.p.K_water3
        * (s.p.T_sSl - s.p.T_wall)
        * (s.p.T_sSl / s.p.T_melt)
        * (1 - pt.exp(ensure_tensor(-(s.p.m_sSl / s.p.m_EAF))))
    )

    # --------------- Liquid Slag ---------------

    # Heat exchange between liquid slag and gas zone
    Q_lSlgas = (
        (s.p.m_lSl / s.p.m_EAF) * s.p.K_therm8 * (s.p.T_lSl - s.p.T_gas) * s.p.K_sSclSc
    )

    # Energy loss in liquid slag due to cooling
    Q_lSlwater = (
        s.p.K_water4
        * (s.p.T_lSl - s.p.T_wall)
        * (s.p.T_lSl / s.p.T_melt)
        * (1 - pt.exp(ensure_tensor(-(s.p.m_lSl / s.p.m_EAF))))
    )

    # ---------------- Gas Zone -----------------

    # Energy received by gas zone from arcs
    Q_arcgas = 0.025 * s.p.P_arc

    # Energy loss from gas zone to furnace roof and walls
    Q_gaswater = s.p.K_water5 * (
        (s.p.T_gas - s.p.T_roof) * (s.p.A1 / (s.p.A1 + s.p.A2))
        + (s.p.T_gas - s.p.T_wall) * (s.p.A2 / (s.p.A1 + s.p.A2))
    )

    # ====================== Reactor Areas ====================

    # Areas of roof and wall
    s.p.A1 = (pt.pi * s.p.r_eafout**2) - (pt.pi * s.p.r_hole**2)  # roof
    s.p.A2 = 2 * pt.pi * s.p.r_eafout * s.p.h_wall  # wall
    s.p.A4 = pt.pi * s.p.r_eafin**2

    # Surface area of sSc and lSc
    A3 = (
        (pt.pi * s.p.r_eafout**2)
        - (pt.pi * (s.p.d_coneout / 2) ** 2)
        + (
            pt.pi
            * 0.75
            * s.p.d_coneout
            * pt.sqrt(ensure_tensor(s.p.h_cone + s.p.d_coneout / 4))
        )
    )

    # ====================== Slag Foaming =====================
    # All from Fruham 1999

    # Slag viscosity
    # Read from the ternary diagram of CaO-FeO-SiO2 system (2.84)
    nu = 0.4

    # Surface tension
    sigma = 0.475  # N/m

    # Rate of Oxidation to CO
    r_CO_ox = r_FeO_CL + r_FeO_CD + r_C_hO2 + r_MnO_C

    # Gas Vol. flowrate and Superficial Gas Velocity
    U_g = (r_CO_ox * 8.314 * s.p.T_gas) / ((s.p.rp + 120000) * s.p.A_eaf)
    U_T = (14.55 * U_g) / (1 - 0.089 * U_g)

    # Bubble Diameter
    # Drag Coeff. Cd assumed unity
    # Bubble velocity 0.7 at U_T = 1.76
    d_b = (3 / (1.14 * s.p.rho_lSc**2)) ** (1 / 3) * ((2 * sigma) / (0.7**2))

    # Slag Foaming Index
    Xi = (
        115 * nu**1.2 / (sigma**0.2 * s.p.rho_lSl * d_b**0.9)
    )  # Taken from Zhang Fruham 1995

    # Height change due to foaming
    dh_slag = Xi * U_g

    # Slag Factor
    K_slag = (
        0.7
        * (0.5 * pt.tanh(ensure_tensor(5 * (s.p.h_lSl + dh_slag) - 1.25)) + 0.5)
        * (0.5 * pt.tanh(ensure_tensor(3.2 * (1 - (s.p.m_sSc / 1000)) - 1.29)) + 0.5)
    )

    # ======================== View Factor =======================

    # =========================
    # ======== Glossary =======
    # =========================
    # ====     1 = Roof    ====
    # ====     2 = Wall    ====
    # ====     3 = sSc     ====
    # ====     4 = lSc     ====
    # ====     5 = arc     ====
    # =========================

    # VF_51 Arc -> Roof
    R = s.p.r_electrode / s.p.r_eafout
    H1 = (s.p.h_electrode + s.p.h_arc) / s.p.r_eafout
    H2 = s.p.h_electrode / s.p.r_eafout
    a1 = H1**2 + R**2 - 1
    a2 = H2**2 + R**2 - 1
    b1 = H1**2 - R**2 + 1
    b2 = H2**2 - R**2 + 1

    VF_511 = (b1 / (8 * R * H1)) + (1 / (2 * pt.pi)) * (
        pt.acos(ensure_tensor(a1 / b1))
        - (1 / (2 * H1))
        * pt.sqrt(ensure_tensor((((a1 + 2) ** 2) / (R**2)) - 4))
        * pt.acos(ensure_tensor((a1 * R) / b1))
        - (a1 / (2 * R * H1)) * pt.sin(ensure_tensor(R))
    )
    VF_512 = (b2 / (8 * R * H2)) + (1 / (2 * pt.pi)) * (
        pt.acos(ensure_tensor(a2 / b2))
        - (1 / (2 * H2))
        * pt.sqrt(ensure_tensor((((a2 + 2) ** 2) / (R**2)) - 4))
        * pt.acos(ensure_tensor((a2 * R) / b2))
        - (a2 / (2 * R * H2)) * pt.sin(ensure_tensor(R))
    )

    A511 = 2 * pt.pi * s.p.r_electrode * (s.p.h_electrode + s.p.h_arc)
    A512 = 2 * pt.pi * s.p.r_electrode * s.p.h_electrode
    A513 = 2 * pt.pi * s.p.r_electrode * s.p.h_arc

    VF_51 = (1 - K_slag) * ((VF_511 * A511 - VF_512 * A512) / A513)

    # VF_52 Arc -> Wall
    X = s.p.h_cone / s.p.r_eafout
    Y = s.p.h_wall / s.p.r_eafout
    L = s.p.h_arc / s.p.r_eafout
    R = s.p.r_electrode / s.p.r_eafout

    aX = X**2 + R**2 - 1
    bX = X**2 - R**2 + 1
    FX = (bX / (8 * R * X)) + (1 / (2 * pt.pi)) * (
        pt.acos(ensure_tensor(aX / bX))
        - (1 / (2 * X))
        * pt.sqrt(ensure_tensor((((aX + 2) ** 2) / (R**2)) - 4))
        * pt.acos(ensure_tensor((aX * R) / bX))
        - (aX / (2 * R * X)) * pt.sin(ensure_tensor(R))
    )
    if pt.isnan(ensure_tensor(FX)):
        FX = 0

    aLX = (L - X) ** 2 + R**2 - 1
    bLX = (L - X) ** 2 - R**2 + 1
    FLX = (bLX / (8 * R * (L - X))) + (1 / (2 * pt.pi)) * (
        pt.acos(ensure_tensor(aLX / bLX))
        - (1 / (2 * (L - X)))
        * pt.sqrt(ensure_tensor((((aLX + 2) ** 2) / (R**2)) - 4))
        * pt.acos(ensure_tensor((aLX * R) / bLX))
        - (aLX / (2 * R * (L - X))) * pt.sin(ensure_tensor(R))
    )

    aYXL = (Y + X - L) ** 2 + R**2 - 1
    bYXL = (Y + X - L) ** 2 - R**2 + 1
    FYXL = (bYXL / (8 * R * (Y + X - L))) + (1 / (2 * pt.pi)) * (
        pt.acos(ensure_tensor(aYXL / bYXL))
        - (1 / (2 * (Y + X - L)))
        * pt.sqrt(ensure_tensor((((aYXL + 2) ** 2) / (R**2)) - 4))
        * pt.acos(ensure_tensor((aYXL * R) / bYXL))
        - (aYXL / (2 * R * (Y + X - L))) * pt.sin(ensure_tensor(R))
    )

    aXY = (X + Y) ** 2 + R**2 - 1
    bXY = (X + Y) ** 2 - R**2 + 1
    FXY = (bXY / (8 * R * (X + Y))) + (1 / (2 * pt.pi)) * (
        pt.acos(ensure_tensor(aXY / bXY))
        - (1 / (2 * (X + Y)))
        * pt.sqrt(ensure_tensor((((aXY + 2) ** 2) / (R**2)) - 4))
        * pt.acos(ensure_tensor((aXY * R) / bXY))
        - (aXY / (2 * R * (X + Y))) * pt.sin(ensure_tensor(R))
    )

    VF_52 = (1 - K_slag) * (
        (X / L) * FX
        + ((L - X) / L) * (1 - FLX)
        + ((Y + X - L) / L) * FYXL
        - ((X + Y) / L) * FXY
    )

    # VF_53 Arc -> sSc
    m_charge = s.p.m_sSc + s.p.m_lSc
    VF_53 = (1 - VF_51 - VF_52) * (1 - s.p.K_sSclSc * (1 - (s.p.m_sSc / m_charge)))

    # VF_54 Arc -> lSc
    VF_54 = (1 - VF_51 - VF_52) * (s.p.K_sSclSc * (1 - (s.p.m_sSc / m_charge)))

    # VF_41 lSc -> Roof
    H = s.p.h_wall / s.p.r_eafin
    R2 = s.p.r_hole / s.p.r_eafin
    R3 = s.p.r_eafout / s.p.r_eafin

    VF_41 = (1 / 2) * (
        R3**2
        - R2**2
        - pt.sqrt(ensure_tensor((1 + R3**2 + H**2) ** 2 - 4 * R3**2))
        + pt.sqrt(ensure_tensor((1 + R2**2 + H**2) ** 2 - 4 * R2**2))
    )

    # VF_14 Roof -> lSc
    VF_14 = VF_41 * (s.p.A4 / s.p.A1)

    # VF_13 Roof -> sSc
    #     H = h_wall / self.parameters.r_hole
    #     R2 = self.parameters.r_eafout / self.parameters.r_hole
    #     R3 = d_coneout/2 / self.parameters.r_hole
    #     R4 = d_conein/2 / self.parameters.r_hole

    #     VF_131 = 1/(2*(R2**2-1)) * (pt.sqrt((R2**2+R3**2+H**2)**2 - (2*R3*R2)**2) - \
    #         pt.sqrt((R2**2+R4**2+H**2)**2 - (2*R2*R4)**2) + pt.sqrt((1+R4**2+H**2)**2 - (2*R4**2)**2) \
    #         - pt.sqrt((1+R3**2+H**2)**2 - (2*R3**2)**2))

    H = s.p.h_cone / (s.p.d_conein / 2)
    R = (s.p.d_coneout / 2) / (s.p.d_conein / 2)
    X = 1 + R**2 + H**2

    VF_132 = (2 * R**2 - X + pt.sqrt(ensure_tensor(X**2 - 4 * R**2))) / (
        2 * pt.sqrt(ensure_tensor(X - 2 * R)) * (1 + R)
    )

    VF_13 = VF_132 * VF_41

    # VF_31 sSc -> Roof
    VF_31 = VF_13 * (s.p.A1 / A3)

    # VF_32 sSc -> Wall
    R = s.p.r_eafout / (s.p.d_coneout / 2)
    H = s.p.h_wall / (s.p.d_coneout / 2)

    VF_321 = (
        VF_132
        * (1 / 2)
        * (1 - R**2 - H**2 + pt.sqrt(ensure_tensor((1 + R**2 + H**2) ** 2 - 4 * R**2)))
    )
    #     VF_322 = (1/2)*(1 + (1/(R**2-1)) * (H*pt.sqrt(4*R**2+H**2) - \
    #         pt.sqrt((1+R**2+H**2)**2 - 4*R**2)))

    VF_32 = VF_321

    # VF_23 Wall -> sSc
    VF_23 = VF_32 * (A3 / s.p.A2)

    # VF_42 lSc -> Wall
    R = s.p.r_eafout / s.p.r_eafin
    H = s.p.h_wall / s.p.r_eafin

    VF_42 = (1 / 2) * (
        1 - R**2 - H**2 + pt.sqrt(ensure_tensor((1 + R**2 + H**2) ** 2 - 4 * R**2))
    )

    # VF_24 Wall -> lSc
    VF_24 = VF_42 * (s.p.A4 / s.p.A2)

    # Inverse
    VF_15 = VF_51 * (A513 / s.p.A1)
    VF_25 = VF_52 * (A513 / s.p.A2)
    VF_35 = VF_53 * (A513 / A3)
    VF_45 = VF_54 * (A513 / s.p.A4)

    # VF_12 Roof -> Wall
    VF_12 = 1 - VF_13 - VF_14 - VF_15

    # VF_21 Wall -> Roof
    VF_21 = VF_12 * (s.p.A1 / s.p.A2)

    # ========================= Radiosity ========================
    Q_arcRAD = 0.75 * s.p.P_arc

    # Radiosity of roof
    s.p.J_roof = s.p.ep1 * s.p.sig * s.p.T_roof**4 / 1000 + (1 - s.p.ep1) * (
        VF_12 * s.p.J_wall + VF_13 * s.p.J_sSc + VF_14 * s.p.J_lSc + VF_15 * Q_arcRAD
    )

    # Radiosity of wall
    s.p.J_wall = s.p.ep2 * s.p.sig * s.p.T_wall**4 / 1000 + (1 - s.p.ep2) * (
        VF_21 * s.p.J_roof + VF_23 * s.p.J_sSc + VF_24 * s.p.J_lSc + VF_25 * Q_arcRAD
    )

    # Radiosity of sSc
    s.p.J_sSc = s.p.ep3 * s.p.sig * s.p.T_sSc**4 / 1000 + (1 - s.p.ep3) * (
        VF_31 * s.p.J_roof + VF_32 * s.p.J_wall + VF_35 * Q_arcRAD
    )

    # Radiosity of lSc
    s.p.J_lSc = s.p.ep4 * s.p.sig * s.p.T_lSc**4 / 1000 + (1 - s.p.ep4) * (
        VF_41 * s.p.J_roof + VF_42 * s.p.J_wall + VF_45 * Q_arcRAD
    )

    # ========================= Radiation ========================
    # Radiative heat flow in roof
    Q_roofRAD = (
        s.p.A1
        * (
            VF_12 * (s.p.J_roof - s.p.J_wall)
            + VF_13 * (s.p.J_roof - s.p.J_sSc)
            + VF_14 * (s.p.J_roof - s.p.J_lSc)
        )
        - VF_51 * Q_arcRAD
    )

    # Radiative heat flow in wall
    Q_wallRAD = (
        s.p.A2
        * (
            VF_21 * (s.p.J_wall - s.p.J_roof)
            + VF_23 * (s.p.J_wall - s.p.J_sSc)
            + VF_24 * (s.p.J_wall - s.p.J_lSc)
        )
        - VF_52 * Q_arcRAD
    )

    # Radiative heat flow in sSc
    Q_sScRAD = (
        A3 * (VF_31 * (s.p.J_sSc - s.p.J_roof) + VF_32 * (s.p.J_sSc - s.p.J_wall))
        - VF_53 * Q_arcRAD
    )

    # Radiative heat flow in lSc
    Q_lScRAD = (
        s.p.A4 * (VF_41 * (s.p.J_lSc - s.p.J_roof) + VF_42 * (s.p.J_lSc - s.p.J_wall))
        - VF_54 * Q_arcRAD
    )

    # ====================== Total Heat Flow =====================

    Q_lScchem = (
        dH_Ta
        + dH_Tb
        + dH_Tc
        + dH_Td
        + dH_Te
        + dH_Tf
        + dH_Tg
        + dH_Ti
        + dH_Tj
        + dH_Tk
        + dH_Tl
        + dH_Tm
        + dH_Tn
    )

    # Net heat flow in solid steel zone (sSc)
    # CO post combustion and Oxygen burner neglected
    Q_sSc = (
        (Q_arc - dH_Th) * (1 - s.p.K_sSclSc)
        + Q_lScsSc
        - Q_sScsSl
        - Q_sSclSl
        - Q_sScgas
        - Q_sScwater
        - Q_sScRAD
    )

    # Net heat flow in liquid metal zone (lSc)
    # CO post combustion and Oxygen burner neglected
    Q_lSc = (
        (Q_arc - dH_Th) * s.p.K_sSclSc
        - Q_lScchem
        - Q_lScsSc
        - Q_lScsSl
        - Q_lSclSl
        - Q_lScgas
        - Q_lScwater
        - Q_lScRAD
    )

    # Net heat flow in solid slag zone
    Q_sSl = Q_sScsSl + Q_lScsSl - Q_sSlwater

    # Net heat flow in liquid slag zone
    Q_lSl = Q_lSclSl + Q_sSclSl - Q_lSlgas - Q_lSlwater

    # Gas zone energy balance
    Q_gas = Q_arcgas + Q_sScgas + Q_lScgas + Q_lSlgas - Q_gaswater

    # ==================== Temperature Change ====================

    # Temperature change of sSc
    dT_sSc = (Q_sSc * (1 - (s.p.T_sSc / s.p.T_melt))) / (
        (s.p.m_sSc / s.p.M_Fe) * s.p.Cp_sSc
    )

    # Temperature change of lSc
    dT_lSc = Q_lSc / ((s.p.m_lSc / s.p.M_Fe) * s.p.Cp_lSc)

    # Temperature change of sSl
    dT_sSl = (Q_sSl * (1 - (s.p.T_sSl / s.p.T_melt))) / (
        (s.p.m_sSl / s.p.M_sSl) * s.p.Cp_sSl
    )

    # Temperature change of gas
    dT_gas = Q_gas / ((m_gas / s.p.M_gas) * s.p.Cp_gas)

    # Temperature change of lSl
    dT_lSl = Q_lSl / ((s.p.m_lSl / s.p.M_lSl) * s.p.Cp_lSl)

    # Temperature change of roof
    dT_roof = (
        -Q_roofRAD
        + (s.p.A1 / (s.p.A1 + s.p.A2)) * Q_gaswater
        - s.p.phi1 * s.p.Cp_H2O * (s.p.T_roof - s.p.T_water)
    ) / (s.p.A1 * s.p.d1 * s.p.rho * s.p.Cp_roof)

    # Temperature change of wall
    dT_wall = (
        -Q_wallRAD
        + (s.p.A2 / (s.p.A1 + s.p.A2)) * Q_gaswater
        - s.p.phi2 * s.p.Cp_H2O * (s.p.T_wall - s.p.T_water)
    ) / (s.p.A2 * s.p.d2 * s.p.rho * s.p.Cp_wall)

    s.p.T_sSc = s.p.T_sSc + dT_sSc * s.p.ts
    s.p.T_sSl = s.p.T_sSl + dT_sSl * s.p.ts
    s.p.T_lSc = s.p.T_lSc + dT_lSc * s.p.ts
    s.p.T_lSl = s.p.T_lSl + dT_lSl * s.p.ts
    s.p.T_gas = s.p.T_gas + dT_gas * s.p.ts
    s.p.T_roof = s.p.T_roof + dT_roof * s.p.ts
    s.p.T_wall = s.p.T_wall + dT_wall * s.p.ts

    # ======================= Phase Change =======================

    # Injected Carbon Dissolve Rate
    dm_CL_melt = (s.p.m_CL * s.p.T_lSc * s.p.Cp_lSc * (s.p.T_air / s.p.T_melt)) / (
        s.p.lambda_C + s.p.Cp_C * (s.p.T_melt - s.p.T_air)
    )

    # Melt rate of solid metal (kg/s)
    dm_sSc = (Q_sSc * (s.p.T_sSc / s.p.T_melt)) / (
        s.p.lambda_sSc + s.p.Cp_sSc * (s.p.T_melt - s.p.T_sSc)
    )
    # T_lSc = (T_lSc * m_lSc + self.parameters.T_melt * dm_sSc * self.parameters.ts) / (m_lSc + dm_sSc * self.parameters.ts)
    s.p.m_Cr_sSc = s.p.m_Cr_sSc - (dm_sSc * MX_Cr_sSc * s.p.ts)
    s.p.m_Cr_lSc = s.p.m_Cr_lSc + (dm_sSc * MX_Cr_sSc * s.p.ts)
    s.p.m_Fe_sSc = s.p.m_Fe_sSc - (dm_sSc * MX_Fe_sSc * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + (dm_sSc * MX_Fe_sSc * s.p.ts)
    s.p.m_Mn_sSc = s.p.m_Mn_sSc - (dm_sSc * MX_Mn_sSc * s.p.ts)
    s.p.m_Mn_lSc = s.p.m_Mn_lSc + (dm_sSc * MX_Mn_sSc * s.p.ts)
    s.p.m_P_sSc = s.p.m_P_sSc - (dm_sSc * MX_P_sSc * s.p.ts)
    s.p.m_P_lSc = s.p.m_P_lSc + (dm_sSc * MX_P_sSc * s.p.ts)
    s.p.m_Si_sSc = s.p.m_Si_sSc - (dm_sSc * MX_Si_sSc * s.p.ts)
    s.p.m_Si_lSc = s.p.m_Si_lSc + (dm_sSc * MX_Si_sSc * s.p.ts)
    s.p.m_C_sSc = s.p.m_C_sSc - (dm_sSc * MX_C_sSc * s.p.ts)
    s.p.m_C_lSc = s.p.m_C_lSc + (dm_sSc * MX_C_sSc * s.p.ts)
    s.p.m_Al2O3_sSc = s.p.m_Al2O3_sSc - (dm_sSc * MX_Al2O3_sSc * s.p.ts)
    s.p.m_Al2O3_lSl = s.p.m_Al2O3_lSl + (dm_sSc * MX_Al2O3_sSc * s.p.ts)
    s.p.m_CaO_sSc = s.p.m_CaO_sSc - (dm_sSc * MX_CaO_sSc * s.p.ts)
    s.p.m_CaO_lSl = s.p.m_CaO_lSl + (dm_sSc * MX_CaO_sSc * s.p.ts)
    s.p.m_SiO2_sSc = s.p.m_SiO2_sSc - (dm_sSc * MX_SiO2_sSc * s.p.ts)
    s.p.m_SiO2_lSl = s.p.m_SiO2_lSl + (dm_sSc * MX_SiO2_sSc * s.p.ts)
    s.p.m_MgO_sSc = s.p.m_MgO_sSc - (dm_sSc * MX_MgO_sSc * s.p.ts)
    s.p.m_MgO_lSl = s.p.m_MgO_lSl + (dm_sSc * MX_MgO_sSc * s.p.ts)
    s.p.m_MnO_sSc = s.p.m_MnO_sSc - (dm_sSc * MX_MnO_sSc * s.p.ts)
    s.p.m_MnO_lSl = s.p.m_MnO_lSl + (dm_sSc * MX_MnO_sSc * s.p.ts)
    s.p.m_P2O5_sSc = s.p.m_P2O5_sSc - (dm_sSc * MX_P2O5_sSc * s.p.ts)
    s.p.m_P2O5_lSl = s.p.m_P2O5_lSl + (dm_sSc * MX_P2O5_sSc * s.p.ts)

    # Melt rate of solid slag (kg/s)
    # Melt temperature of 1400C according to https://core.ac.uk/download/pdf/82678298.pdf
    dm_sSl = (Q_sSl * (s.p.T_sSl / 1673)) / (
        (s.p.lambda_sSl + s.p.Cp_sSl * (1673 - s.p.T_sSl)) / s.p.M_sSl
    )

    # T_lSl = (T_lSl * m_lSl + 1673 * dm_sSl * self.parameters.ts) / (m_lSl + dm_sSl * self.parameters.ts)

    s.p.m_Al2O3_sSl = s.p.m_Al2O3_sSl - (dm_sSl * MX_Al2O3_sSl * s.p.ts)
    s.p.m_Al2O3_lSl = s.p.m_Al2O3_lSl + (dm_sSl * MX_Al2O3_sSl * s.p.ts)
    s.p.m_CaO_sSl = s.p.m_CaO_sSl - (dm_sSl * MX_CaO_sSl * s.p.ts)
    s.p.m_CaO_lSl = s.p.m_CaO_lSl + (dm_sSl * MX_CaO_sSl * s.p.ts)
    s.p.m_MgO_sSl = s.p.m_MgO_sSl - (dm_sSl * MX_MgO_sSl * s.p.ts)
    s.p.m_MgO_lSl = s.p.m_MgO_lSl + (dm_sSl * MX_MgO_sSl * s.p.ts)
    s.p.m_SiO2_sSl = s.p.m_SiO2_sSl - (dm_sSl * MX_SiO2_sSl * s.p.ts)
    s.p.m_SiO2_lSl = s.p.m_SiO2_lSl + (dm_sSl * MX_SiO2_sSl * s.p.ts)

    # ===================== Geometry Change ======================

    # height of liquid metal
    s.p.h_lSc = (s.p.m_lSc / s.p.rho_lSc) / s.p.A_bath

    # height of liquid slag
    s.p.h_lSl = (s.p.m_lSl / s.p.rho_lSl) / s.p.A_bath

    s.p.h_sSc2 = 0
    s.p.d_conein = s.p.r_eafin * 2
    s.p.d_coneout = s.p.r_eafout * 2

    s.p.V_sSc = s.p.m_sSc / s.p.rho_sSc
    s.p.h_cone = s.p.V_sSc / (
        pt.pi * s.p.r_eafout**2
        - (1 / 3)
        * pt.pi
        * (s.p.r_eafin**2 + s.p.r_eafin * s.p.r_eafout + s.p.r_eafout**2)
    )
    s.p.h_sSc1 = s.p.h_cone

    # Arc height
    s.p.h_arc = s.p.h_eafup - s.p.h_electrode - (s.p.h_lSc + s.p.h_lSl)

    # height of wall
    s.p.h_wall = s.p.h_eafup + s.p.h_eaflow - s.p.h_sSc1 - s.p.h_lSc - s.p.h_lSl

    # pt.exposure Coeff.
    s.p.K_sSclSc = (
        0.5
        * pt.tanh(ensure_tensor(5 * (s.p.h_lSc - s.p.h_sSc1 - s.p.h_sSc2 + s.p.h_cone)))
        + 0.5
    )

    # =================== Reaction Mass Change ===================

    # Injected carbon dissolution
    s.p.m_CL = s.p.m_CL - (dm_CL_melt * s.p.ts)
    s.p.m_C_lSc = s.p.m_C_lSc + (dm_CL_melt * s.p.ts)

    # ---------- Decarburization ---------
    # FeO + C -> Fe + CO

    # By injected carbon
    s.p.m_FeO_lSl = s.p.m_FeO_lSl - (r_FeO_CL * s.p.M_FeO * s.p.ts)
    s.p.m_CL = s.p.m_CL - (r_FeO_CL * s.p.M_C * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + (r_FeO_CL * s.p.M_Fe * s.p.ts)
    s.p.m_CO = s.p.m_CO + (r_FeO_CL * s.p.M_CO * s.p.ts)

    # By dissolved carbon
    s.p.m_FeO_lSl = s.p.m_FeO_lSl - (r_FeO_CD * s.p.M_FeO * s.p.ts)
    s.p.m_C_lSc = s.p.m_C_lSc - (r_FeO_CD * s.p.M_C * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + (r_FeO_CD * s.p.M_Fe * s.p.ts)
    s.p.m_CO = s.p.m_CO + (r_FeO_CD * s.p.M_CO * s.p.ts)

    # ---------- Carbon Oxidation -----------

    # To carbon monoxide
    # C + 1/2 O2 -> CO
    s.p.m_C_lSc = s.p.m_C_lSc - (r_C_hO2 * s.p.M_C * s.p.ts)
    s.p.m_CO = s.p.m_CO + (r_C_hO2 * s.p.M_CO * s.p.ts)
    s.p.m_O2 = s.p.m_O2 - 0.5 * (r_C_hO2 * s.p.M_O2 * s.p.ts)

    # To carbon dioxide
    # C + O2 -> CO2
    s.p.m_C_lSc = s.p.m_C_lSc - (r_C_O2 * s.p.M_C * s.p.ts)
    s.p.m_CO2 = s.p.m_CO2 + (r_C_O2 * s.p.M_CO2 * s.p.ts)
    s.p.m_O2 = s.p.m_O2 - (r_C_O2 * s.p.M_O2 * s.p.ts)

    # -------- MnO Decarburization ----------

    # MnO + C -> Mn + CO

    s.p.m_MnO_lSl = s.p.m_MnO_lSl - (r_MnO_C * s.p.M_MnO * s.p.ts)
    s.p.m_C_lSc = s.p.m_C_lSc - (r_MnO_C * s.p.M_C * s.p.ts)
    s.p.m_Mn_lSc = s.p.m_Mn_lSc + (r_MnO_C * s.p.M_Mn * s.p.ts)
    s.p.m_CO = s.p.m_CO + (r_MnO_C * s.p.M_CO * s.p.ts)

    # ----------- Desiliconization ----------

    # 2FeO + Si -> 2Fe + SiO2

    s.p.m_FeO_lSl = s.p.m_FeO_lSl - 2 * (r_2FeO_Si * s.p.M_FeO * s.p.ts)
    s.p.m_Si_lSc = s.p.m_Si_lSc - (r_2FeO_Si * s.p.M_Si * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + 2 * (r_2FeO_Si * s.p.M_Fe * s.p.ts)
    s.p.m_SiO2_lSl = s.p.m_SiO2_lSl + (r_2FeO_Si * s.p.M_SiO2 * s.p.ts)

    # --------- Silicon Oxidation ---------

    # Si + O2 -> SiO2

    s.p.m_Si_lSc = s.p.m_Si_lSc - (r_Si_O2 * s.p.M_Si * s.p.ts)
    s.p.m_SiO2_lSl = s.p.m_SiO2_lSl + (r_Si_O2 * s.p.M_SiO2 * s.p.ts)
    s.p.m_O2 = s.p.m_O2 - (r_Si_O2 * s.p.M_O2 * s.p.ts)

    # ------- Si reaction with MnO --------

    # 2MnO + Si -> 2Mn + SiO2

    s.p.m_MnO_lSl = s.p.m_MnO_lSl - 2 * (r_2MnO_Si * s.p.M_MnO * s.p.ts)
    s.p.m_Si_lSc = s.p.m_Si_lSc - (r_2MnO_Si * s.p.M_Si * s.p.ts)
    s.p.m_Mn_lSc = s.p.m_Mn_lSc + 2 * (r_2MnO_Si * s.p.M_Mn * s.p.ts)
    s.p.m_SiO2_lSl = s.p.m_SiO2_lSl + (r_2MnO_Si * s.p.M_SiO2 * s.p.ts)

    # ------- Mn reaction with FeO ---------

    # Mn + FeO -> MnO + Fe

    s.p.m_Mn_lSc = s.p.m_Mn_lSc - (r_FeO_Mn * s.p.M_Mn * s.p.ts)
    s.p.m_FeO_lSl = s.p.m_FeO_lSl - (r_FeO_Mn * s.p.M_FeO * s.p.ts)
    s.p.m_MnO_lSl = s.p.m_MnO_lSl + (r_FeO_Mn * s.p.M_MnO * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + (r_FeO_Mn * s.p.M_Fe * s.p.ts)

    # ------- Cr reaction with FeO ---------

    # 3FeO + 2Cr -> 3Fe + Cr2O3

    s.p.m_FeO_lSl = s.p.m_FeO_lSl - 1.5 * (r_3FeO_2Cr * s.p.M_FeO * s.p.ts)
    s.p.m_Cr_lSc = s.p.m_Cr_lSc - (r_3FeO_2Cr * s.p.M_Cr * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + 1.5 * (r_3FeO_2Cr * s.p.M_Fe * s.p.ts)
    s.p.m_Cr2O3_lSl = s.p.m_Cr2O3_lSl + 0.5 * (r_3FeO_2Cr * s.p.M_Cr2O3 * s.p.ts)

    # --------- Chromium Oxidation ---------

    # 2Cr + 3/2O2 -> Cr2O3

    s.p.m_Cr_lSc = s.p.m_Cr_lSc - (r_2Cr_3hO2 * s.p.M_Cr * s.p.ts)
    s.p.m_Cr2O3_lSl = s.p.m_Cr2O3_lSl + 0.5 * (r_2Cr_3hO2 * s.p.M_Cr2O3 * s.p.ts)
    s.p.m_O2 = s.p.m_O2 - 1.5 * (r_2Cr_3hO2 * s.p.M_O2 * s.p.ts)

    # -------- Phosphorus Oxidation --------

    # 5FeO + 2P -> 5Fe + P2O5

    s.p.m_FeO_lSl = s.p.m_FeO_lSl - 2.5 * (r_5FeO_2P * s.p.M_FeO * s.p.ts)
    s.p.m_P_lSc = s.p.m_P_lSc - (r_5FeO_2P * s.p.M_P * s.p.ts)
    s.p.m_Fe_lSc = s.p.m_Fe_lSc + 2.5 * (r_5FeO_2P * s.p.M_Fe * s.p.ts)
    s.p.m_P2O5_lSl = s.p.m_P2O5_lSl + 0.5 * (r_5FeO_2P * s.p.M_P2O5 * s.p.ts)

    # ------------- Fe Oxidation -------------

    # Fe + 1/2O2 -> FeO

    s.p.m_Fe_lSc = s.p.m_Fe_lSc - (r_Fe_hO2 * s.p.M_Fe * s.p.ts)
    s.p.m_FeO_lSl = s.p.m_FeO_lSl + (r_Fe_hO2 * s.p.M_FeO * s.p.ts)
    s.p.m_O2 = s.p.m_O2 - 0.5 * (r_Fe_hO2 * s.p.M_O2 * s.p.ts)

    # ------------- Combustion ---------------

    # C9H20 + 14O2 -> 9CO2 + 10H2O

    s.p.m_comb_sSc = s.p.m_comb_sSc - (r_comb * s.p.M_C9H20 * s.p.ts)
    s.p.m_O2 = s.p.m_O2 - 14 * (r_comb * s.p.M_O2 * s.p.ts)
    s.p.m_CO2 = s.p.m_CO2 + 9 * (r_comb * s.p.M_CO2 * s.p.ts)
    s.p.m_H2O = s.p.m_H2O + 10 * (r_comb * s.p.M_H2O * s.p.ts)

    # ----------- Post Combustion ------------

    # CO + 1/2O2 -> CO2

    s.p.m_O2 = s.p.m_O2 - (r_post * s.p.M_O2) * s.p.ts
    s.p.m_CO = s.p.m_CO - 2 * (r_post * s.p.M_CO * s.p.ts)
    s.p.m_CO2 = s.p.m_CO2 + 2 * (r_post * s.p.M_CO2 * s.p.ts)

    # --------- Electrode Oxidation ----------

    # C + O2 -> CO2             C here is from electrode so no eq needed

    s.p.m_O2 = s.p.m_O2 - ((dm_el * s.p.M_O2) / s.p.M_C) * s.p.ts
    s.p.m_CO2 = s.p.m_CO2 + ((dm_el * s.p.M_CO2) / s.p.M_C) * s.p.ts

    # ======================= Material Addition ======================

    # ------------ Solid Metal ------------

    # Total mass of solid metal
    s.p.m_sSc = (
        s.p.m_Fe_sSc
        + s.p.m_C_sSc
        + s.p.m_Cr_sSc
        + s.p.m_Mn_sSc
        + s.p.m_P_sSc
        + s.p.m_SiO2_sSc
        + s.p.m_Al2O3_sSc
        + s.p.m_CaO_sSc
        + s.p.m_MgO_sSc
        + s.p.m_MnO_sSc
        + s.p.m_Si_sSc
        + s.p.m_comb_sSc
    )

    # Addition of DRI
    s.p.m_Fe_sSc = s.p.m_Fe_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_Fe_DRI
    s.p.m_C_sSc = s.p.m_C_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_C_DRI
    s.p.m_SiO2_sSc = s.p.m_SiO2_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_SiO2_DRI
    s.p.m_Al2O3_sSc = s.p.m_Al2O3_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_Al2O3_DRI
    s.p.m_CaO_sSc = s.p.m_CaO_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_CaO_DRI
    s.p.m_MgO_sSc = s.p.m_MgO_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_MgO_DRI
    s.p.m_MnO_sSc = s.p.m_MnO_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_MnO_DRI
    s.p.m_P2O5_sSc = s.p.m_P2O5_sSc + (s.p.DRI_add * s.p.ts) * s.p.MX_P2O5_DRI

    # Addition of scrap
    s.p.m_Fe_sSc = s.p.m_Fe_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_Fe_scr
    s.p.m_C_sSc = s.p.m_C_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_C_scr
    s.p.m_Si_sSc = s.p.m_Si_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_Si_scr
    s.p.m_Cr_sSc = s.p.m_Cr_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_Cr_scr
    s.p.m_P_sSc = s.p.m_P_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_P_scr
    s.p.m_Mn_sSc = s.p.m_Mn_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_Mn_scr
    s.p.m_comb_sSc = s.p.m_comb_sSc + (s.p.scr_add * s.p.ts) * s.p.MX_comb_scr

    s.p.T_sSc = (
        s.p.T_sSc * s.p.m_sSc
        + s.p.T_scr * s.p.scr_add * s.p.ts
        + s.p.T_DRI * s.p.DRI_add * s.p.ts
    ) / (s.p.m_sSc + s.p.slg_add * s.p.ts + s.p.DRI_add * s.p.ts)

    # ------------ Solid Slag ------------
    s.p.m_CaO_sSl = s.p.m_CaO_sSl + (s.p.slg_add * s.p.ts) * s.p.MX_CaO_slg
    s.p.m_MgO_sSl = s.p.m_MgO_sSl + (s.p.slg_add * s.p.ts) * s.p.MX_MgO_slg
    s.p.m_SiO2_sSl = s.p.m_SiO2_sSl + (s.p.slg_add * s.p.ts) * s.p.MX_SiO2_slg
    s.p.m_Al2O3_sSl = s.p.m_Al2O3_sSl + (s.p.slg_add * s.p.ts) * s.p.MX_Al2O3_slg

    s.p.T_sSl = (s.p.T_sSl * s.p.m_sSl + s.p.T_slg * s.p.slg_add * s.p.ts) / (
        s.p.m_sSl + s.p.slg_add * s.p.ts
    )

    # ------ Extra Material Addition -----

    # Oxygen Lance
    s.p.m_O2 = s.p.m_O2 + s.p.O2_lance * s.p.ts

    # Oxygen Post
    s.p.m_O2 = s.p.m_O2 + s.p.O2_post * s.p.ts

    s.p.T_gas = (
        s.p.T_gas * m_gas
        + s.p.T_air * s.p.O2_lance * s.p.ts
        + s.p.T_air * s.p.O2_post * s.p.ts
    ) / (m_gas + s.p.O2_lance * s.p.ts + s.p.O2_post * s.p.ts)

    # Carbon injection
    s.p.m_CL = s.p.m_CL + (s.p.C_inj * s.p.ts)

    # Ferro-Manganese Injection
    s.p.m_Mn_sSc = s.p.m_Mn_sSc + (s.p.FM_inj * s.p.MX_Mn_FM * s.p.ts)
    s.p.m_C_sSc = s.p.m_C_sSc + (s.p.FM_inj * s.p.MX_C_FM * s.p.ts)
    s.p.m_P_sSc = s.p.m_P_sSc + (s.p.FM_inj * s.p.MX_P_FM * s.p.ts)
    s.p.m_Si_sSc = s.p.m_Si_sSc + (s.p.FM_inj * s.p.MX_Si_FM * s.p.ts)
    s.p.m_Fe_sSc = s.p.m_Fe_sSc + (s.p.FM_inj * s.p.MX_Fe_FM * s.p.ts)

    # ======================== Take out ========================
    #     thres_gas = (121590*self.parameters.V_gas) / (R * self.parameters.T_gas)
    #
    #     if XM_gas > thres_gas:
    #         gas_out = XM_gas - thres_gas
    #         H2O_out = gas_out * X_H2O
    #         CO2_out = gas_out * X_CO2
    #         CO_out = gas_out * X_CO
    #         O2_out = gas_out * X_O2
    #
    #         self.parameters.m_H2O = self.parameters.m_H2O - (H2O_out*self.parameters.M_H2O)
    #         self.parameters.m_CO2 = self.parameters.m_CO2 - (CO2_out*self.parameters.M_CO2)
    #         self.parameters.m_CO = self.parameters.m_CO - (CO_out*self.parameters.M_CO)
    #         self.parameters.m_O2 = self.parameters.m_O2 - (O2_out*self.parameters.M_O2)
    #
    #         self.parameters.T_gas = (T_gas * XM_gas + self.parameters.T_air * gas_out) / (XM_gas + gas_out)
    #

    # Off gas venting
    s.p.m_CO = (
        s.p.m_CO - (s.p.hd * s.p.u1 * MX_CO) / (s.p.K_U * s.p.u2 + s.p.hd) * s.p.ts
    )
    s.p.m_CO2 = (
        s.p.m_CO2 - (s.p.hd * s.p.u1 * MX_CO2) / (s.p.K_U * s.p.u2 + s.p.hd) * s.p.ts
    )
    s.p.m_O2 = (
        s.p.m_O2 - (s.p.hd * s.p.u1 * MX_O2) / (s.p.K_U * s.p.u2 + s.p.hd) * s.p.ts
    )
    s.p.m_H2O = (
        s.p.m_H2O - (s.p.hd * s.p.u1 * MX_H2O) / (s.p.K_U * s.p.u2 + s.p.hd) * s.p.ts
    )

    dm_CO = (
        r_FeO_CL * s.p.M_CO
        + r_FeO_CD * s.p.M_CO
        + r_C_hO2 * s.p.M_CO
        + r_MnO_C * s.p.M_MnO
        - 2 * r_post * s.p.M_CO
    )
    dm_CO2 = (
        r_C_O2 * s.p.M_CO2
        + 9 * r_comb * s.p.M_CO2
        + 2 * r_post * s.p.M_CO2
        + dm_el * s.p.M_CO2 / s.p.M_C
    )
    dm_O2 = (
        s.p.O2_lance
        - 0.5 * r_C_hO2 * s.p.M_O2
        - r_C_O2 * s.p.M_O2
        - r_Si_O2 * s.p.M_O2
        - 1.5 * r_2Cr_3hO2 * s.p.M_O2
        - 14 * r_comb * s.p.M_O2
        + s.p.O2_post
        - r_post * s.p.M_O2
    )
    dm_H2O = 10 * r_comb * s.p.M_H2O

    s.p.rp = (R * s.p.T_gas / s.p.V_gas) * (
        dm_CO / s.p.M_CO + dm_CO2 / s.p.M_CO2 + dm_O2 / s.p.M_O2 + dm_H2O / s.p.M_H2O
    ) + (R * dT_gas / s.p.V_gas) * (
        s.p.m_CO / s.p.M_CO
        + s.p.m_CO2 / s.p.M_CO2
        + s.p.m_O2 / s.p.M_O2
        + s.p.m_H2O / s.p.M_H2O
    )

    if s.step % (s.p.out // s.p.ts) == 0 and s.step != 0:
        sec = s.step * s.p.ts
        # Take out liquid metal
        lSc_out = s.p.m_lSc * 0.5
        s.p.m_Fe_lSc = s.p.m_Fe_lSc - lSc_out * s.p.MX_Fe_lSc
        s.p.m_C_lSc = s.p.m_C_lSc - lSc_out * s.p.MX_C_lSc
        s.p.m_Si_lSc = s.p.m_Si_lSc - lSc_out * s.p.MX_Si_lSc
        s.p.m_Cr_lSc = s.p.m_Cr_lSc - lSc_out * s.p.MX_Cr_lSc
        s.p.m_Mn_lSc = s.p.m_Mn_lSc - lSc_out * s.p.MX_Mn_lSc
        s.p.m_P_lSc = s.p.m_P_lSc - lSc_out * s.p.MX_P_lSc

        # Take out liquid slag
        lSl_out = s.p.m_lSl * 0.5
        s.p.m_Al2O3_lSl = s.p.m_Al2O3_lSl - lSl_out * s.p.MX_Al2O3_lSl
        s.p.m_CaO_lSl = s.p.m_CaO_lSl - lSl_out * s.p.MX_CaO_lSl
        s.p.m_Cr2O3_lSl = s.p.m_Cr2O3_lSl - lSl_out * s.p.MX_Cr2O3_lSl
        s.p.m_FeO_lSl = s.p.m_FeO_lSl - lSl_out * s.p.MX_FeO_lSl
        s.p.m_MgO_lSl = s.p.m_MgO_lSl - lSl_out * s.p.MX_MgO_lSl
        s.p.m_MnO_lSl = s.p.m_MnO_lSl - lSl_out * s.p.MX_MnO_lSl
        s.p.m_P2O5_lSl = s.p.m_P2O5_lSl - lSl_out * s.p.MX_P2O5_lSl
        s.p.m_SiO2_lSl = s.p.m_SiO2_lSl - lSl_out * s.p.MX_SiO2_lSl

        s.out_states.append(TakeoutAnalysis(s.p, sec))
    s.p.recalc_MX_lSc()
    # ===================== For Graph =======================
    if s.step % (1 / s.p.ts) == 0:
        sec = int(s.step * s.p.ts)
        # print(f"{sec}/{s.p.secs}")
        s.gas_temp[sec] = s.p.T_gas
        s.sSc_temp[sec] = s.p.T_sSc
        s.sSl_temp[sec] = s.p.T_sSl
        s.lSc_temp[sec] = s.p.T_lSc
        s.lSl_temp[sec] = s.p.T_lSl
        s.steel_Fe[sec] = s.p.MX_Fe_lSc
        s.m_solid[sec] = s.p.m_sSc
        s.m_liquid[sec] = s.p.m_lSc
        s.m_solid_slag[sec] = s.p.m_sSl
        s.m_liquid_slag[sec] = s.p.m_lSl
        s.rel_pres[sec] = s.p.rp

    s.step += 1
    return [getattr(s.p,n) for n in s.p.x_names+s.p.observer_names+(s.p.y_name,)]
