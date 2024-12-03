import csv
import sys
from constraint import Problem, AllDifferentConstraint


def load_data(filepath):
    '''Cargar datos del archivo recibido (primer argumento)'''
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Parse data
    franjas = int(lines[0].strip())
    matrix_size = tuple(map(int, lines[1].strip().split('x')))
    print(franjas, matrix_size)

    talleres_std = [
    tuple(map(int, pos.strip("()").split(",")))
    for pos in lines[2].split(":")[1].strip().split()
    ] # Crea ua lista de tuplas
    print("talleres_std: ", talleres_std)

    talleres_spc = [
    tuple(map(int, pos.strip("()").split(",")))
    for pos in lines[3].split(":")[1].strip().split()
    ] 
    print("talleres_spc: ", talleres_spc)

    parkings = [
    tuple(map(int, pos.strip("()").split(",")))
    for pos in lines[4].split(":")[1].strip().split()
    ] 
    print("parkings: ", parkings)

    # En la línea 6 y posteriores se indica la info de los aviones, split nos deja la lista ['1', 'JMB', 'T', '2', '2']
    aviones = [line.strip().split('-') for line in lines[5:]] 
    print("aviones: ", aviones)
    
    return franjas, matrix_size, talleres_std, talleres_spc, parkings, aviones

def main(filepath):
    # Load data
    franjas, matriz_size, talleres_std, talleres_spc, parkings, aviones = load_data(filepath)
    
    # Variables
    problem = Problem()
    avion_ids = [avion[0] for avion in aviones]
    franjas_horarias = range(franjas)
    talleres = {'STD': talleres_std, 'SPC': talleres_spc, 'PRK': parkings}
    print("avion_ids: ", avion_ids)
    print("franjas: ", franjas)
    print("franjas_horarias: ", franjas_horarias)
    print("talleres: ", talleres)
    
    for avion_id in avion_ids:
        for franja in franjas_horarias:
            problem.addVariable(f"{avion_id}_franja_{franja}", talleres['STD'] + talleres['SPC'] + talleres['PRK'])
    
    
    variables = [f"{avion_id}_franja_{franja}" for avion_id in avion_ids for franja in franjas_horarias]
    print("VARS\n", variables)

    for variable, domain in problem._variables.items():
        print(f"Variable: {variable}, Domain: {domain}")

    # Restricción 1: Un único taller/parking por franja horaria
    # Está implicito en el modelo que todas las variables toman un único valor, ni más ni menos
    
    
    # Restricción 2: Capacidad de los talleres
    '''for franja in franjas_horarias:
        for taller in talleres['STD'] + talleres['SPC']:
            def capacity_constraint(*assignments):
                std_count = sum(1 for avion in aviones  # ['1', 'JMB', 'T', '2', '2']
                                if f"{avion[0]}_franja_{franja}" in assignments and avion[1] == 'STD')
                                #if f"{a_id}_franja_{franja}" == taller and tipo == 'STD')
                jumbo_count = sum(1 for avion in aviones 
                                if f"{avion[0]}_franja_{franja}" in assignments and avion[1] == 'JMB')
                                #if f"{a_id}_franja_{franja}" == taller and tipo == 'JMB')
                
                # Máximo 2 aviones en total, y como máximo 1 de tipo JUMBO
                return std_count + jumbo_count <= 2 and jumbo_count <= 1
            
            variables = [f"{avion_id}_franja_{franja}" for avion_id in avion_ids]
            problem.addConstraint(capacity_constraint, variables)'''



    # Restricción 2: Capacidad de los talleres
    
    for franja in franjas_horarias:
        def capacity_constraint(*vars):
            # Contar cuántos aviones 'STD' están asignados al taller y franja actuales
            std_count = sum(1 for avion in aviones # avion = ['1', 'JMB', 'T', '2', '2']
                            if f"{avion[0]}_franja_{franja}" == vars and avion[1] == 'STD') # Si se asigna el avión y es STD ??? #TODO

            # Contar cuántos aviones 'JMB' están asignados al taller y franja actuales
            jmb_count = sum(1 for avion in aviones
                            if f"{avion[0]}_franja_{franja}" == vars and avion[1] == 'JMB')

            # Restricción: máximo 2 aviones en total, y como máximo 1 JMB
            return std_count + jmb_count <= 2 and jmb_count <= 1

        # Variables correspondientes a esa franja horaria
        vars = [f"{avion_id}_franja_{franja}" for avion_id in avion_ids]
        #problem.addConstraint(capacity_constraint, vars)


    # Restricción 3: Tareas de mantenimiento
    for avion_id, tipo, restr, t1, t2 in aviones:
        t1, t2 = int(t1), int(t2)
        
        if t2 > 0:
            vars = [f"{avion_id}_franja_{franja}" for franja in franjas_horarias]
            problem.addConstraint(
                lambda *assignments: sum(1 for a in assignments if a in talleres_spc) >= t2, 
                vars
            )


    
    # Restricción 4: las tareas tipo 2 deben hacerse primero si el avión es de rest 'T'
    def verificar_orden_tareas(asignaciones, t1, t2):
        """
        Verifica que las tareas especializadas (tipo 2) se realicen antes que las tareas estándar (tipo 1)
        """
        # Las primeras t2 franjas deben ser asignadas a talleres SPC
        for i in range(t2):
            if asignaciones[i] not in talleres_spc:
                return False  # Si alguna tarea SPC no está en un taller SPC, no cumple la restricción
        
        return True  
    
    for avion_id, tipo, restr, t1, t2 in aviones:
        t1, t2 = int(t1), int(t2) 
        
        if restr == 'T' and t2 > 0:  

            vars_avion = [f"{avion_id}_franja_{franja}" for franja in franjas_horarias]
            
            problem.addConstraint(
                verificar_orden_tareas,  
                vars_avion + [t1, t2]  # Pasamos los talleres SPC, t1, y t2 como argumentos
            )        

    
    # Restricción 5 y 6: Maniobrabilidad y adyacencia
    for franja in franjas_horarias:
        for taller in talleres['STD'] + talleres['SPC'] + talleres['PRK']:
            adjacentes = [
                (taller[0] - 1, taller[1]), (taller[0] + 1, taller[1]),
                (taller[0], taller[1] - 1), (taller[0], taller[1] + 1)
            ]
            adjacentes = [a for a in adjacentes if a in talleres['STD'] + talleres['SPC'] + talleres['PRK']]
            def adjacency_constraint(*assignments):
                return all(a not in adjacentes for a in assignments)
            
            variables = [f"{avion_id}_franja_{franja}" for avion_id in avion_ids]
            #problem.addConstraint(adjacency_constraint, variables)
    
    # Solve problem
    print("x")
    solutions = problem.getSolutions()
    print(solutions)
    print("Ya")

    # Output result
    output_file = filepath.split('.')[0] + ".csv"
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([f"{len(solutions)} soluciones encontradas"])
        for solution in solutions[:5]:  # Limitar a 5 soluciones
            writer.writerow([solution])
    
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python CSPMaintenance.py <path maintenance>")
    else:
        main(sys.argv[1])

'''
Lo que se imprime
4 (5, 5)
talleres_std:  [(0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (3, 3), (4, 1), (4, 2)]
talleres_spc:  [(0, 3), (2, 1), (2, 3), (3, 0), (3, 3)]
parkings:  [(0, 0), (0, 2), (0, 4), (1, 4), (2, 4), (3, 1), (3, 2), (3, 4), (4, 0), (4, 4)]
aviones:  [['1', 'JMB', 'T', '2', '2'], ['2', 'STD', 'F', '1', '3'], ['3', 'STD', 'F', '3', '0'], ['4', 'JMB', 'T', '1', '1'], ['5', 'STD', 'F', '2', '2']]
avion_ids:  ['1', '2', '3', '4', '5']
franjas:  4
franjas_horarias:  range(0, 4)
talleres:  {'STD': [(0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (3, 3), (4, 1), (4, 2)], 'SPC': [(0, 3), (2, 1), 
(2, 3), (3, 0), (3, 3)], 'PRK': [(0, 0), (0, 2), (0, 4), (1, 4), (2, 4), (3, 1), (3, 2), (3, 4), (4, 0), (4, 4)]}
'''