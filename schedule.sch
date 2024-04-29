# this makes the lights turn to their unacceptable state "off"
off_light(1) @ [5]:*    
on_light(2) @ [5]:*     
perturb_slider(1) @ [5]:*     





# these determine the burning of fuel in the two main tanks
burn_fuel("a", 10) @ [0.1]:*
burn_fuel("b", 10) @ [0.1]:*

# these determine the flow of the pumps (when they are "on")
pump_fuel("fd", 20) @ [0.1]:*
pump_fuel("fb", 20) @ [0.1]:*
pump_fuel("db", 20) @ [0.1]:*
pump_fuel("ec", 20) @ [0.1]:*
pump_fuel("ea", 20) @ [0.1]:*
pump_fuel("ca", 20) @ [0.1]:*
pump_fuel("ba", 20) @ [0.1]:*
pump_fuel("ab", 20) @ [0.1]:*