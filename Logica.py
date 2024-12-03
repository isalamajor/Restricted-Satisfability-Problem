import csv
import sys
from constraint import Problem, MaxSumConstraint


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
    ] # Crea una lista de tuplas
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
    
    # Definir variables binarias para cada combinación de avión, franja horaria y taller
    for avion_id in avion_ids:
        for franja in franjas_horarias:
            for tipo_taller in ['STD', 'SPC', 'PRK']:
                # Asignamos una variable binaria (0 o 1) para cada avión, franja y tipo de taller
                for taller in talleres[tipo_taller]:
                    variable_name = f"{avion_id}_franja_{franja}_taller_{taller}"
                    problem.addVariable(variable_name, [0, 1])
    
    # Restricción 1: Un único taller/parking por franja horaria
    for franja in franjas_horarias:
        for avion_id in avion_ids:
            # Cada avión debe estar asignado a exactamente un taller o parking en cada franja horaria
            variables = [f"{avion_id}_franja_{franja}_taller_{taller}" for taller in talleres['STD'] + talleres['SPC'] + talleres['PRK']]
            problem.addConstraint(MaxSumConstraint(1), variables)
    
    # Restricción 2: Capacidad de los talleres
    for franja in franjas_horarias:
        for taller in talleres['STD'] + talleres['SPC']:
            def capacity_constraint(*assignments):
                # Contar cuántos aviones 'STD' están asignados al taller y franja actuales
                std_count = sum(1 for i, avion in enumerate(aviones)
                                if f"{avion[0]}_franja_{franja}_taller_{taller}" == assignments[i] and avion[1] == 'STD')

                # Contar cuántos aviones 'JMB' están asignados al taller y franja actuales
                jumbo_count = sum(1 for i, avion in enumerate(aviones)
                                if f"{avion[0]}_franja_{franja}_taller_{taller}" == assignments[i] and avion[1] == 'JMB')

                # Restricción: máximo 2 aviones en total, y como máximo 1 JMB
                return std_count + jumbo_count <= 2 and jumbo_count <= 1

            # Variables correspondientes a esa franja horaria y taller
            variables = [f"{avion[0]}_franja_{franja}_taller_{taller}" for avion in aviones]
            problem.addConstraint(capacity_constraint, variables)

    # Restricción 3: Tareas de mantenimiento
    for avion_id, tipo, restr, t1, t2 in aviones:
        t1, t2 = int(t1), int(t2)
        if restr == 'T':
            variables = [f"{avion_id}_franja_{franja}" for franja in range(t1)]
            problem.addConstraint(lambda *assignments: all(a in talleres['SPC'] for a in assignments), variables)
            variables = [f"{avion_id}_franja_{franja}" for franja in range(t1, t1 + t2)]
            problem.addConstraint(lambda *assignments: all(a in talleres['STD'] for a in assignments), variables)

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
            # problem.addConstraint(adjacency_constraint, variables)
    
    # Solve problem
    print("x")
    solutions = problem.getSolutions()
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
