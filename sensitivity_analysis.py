import pm4py
import time
import matplotlib.pyplot as plt
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
import graphviz

def custom_dag_to_petri_net(nodes, edges, start_nodes, end_nodes):
    net = PetriNet("Hybrid_DAG_Petri_Net")
    node_places = {}
    for node_id, activity_label in nodes.items():
        t = PetriNet.Transition(name=str(node_id), label=str(activity_label))
        net.transitions.add(t)
        p_in = PetriNet.Place(f"p_in_{node_id}")
        p_out = PetriNet.Place(f"p_out_{node_id}")
        net.places.add(p_in)
        net.places.add(p_out)
        petri_utils.add_arc_from_to(p_in, t, net)
        petri_utils.add_arc_from_to(t, p_out, net)
        node_places[node_id] = {'in': p_in, 'out': p_out}

    for index, (src, dst) in enumerate(edges):
        tau = PetriNet.Transition(name=f"tau_{src}_{dst}_{index}", label=None)
        net.transitions.add(tau)
        petri_utils.add_arc_from_to(node_places[src]['out'], tau, net)
        petri_utils.add_arc_from_to(tau, node_places[dst]['in'], net)

    source = PetriNet.Place("source")
    sink = PetriNet.Place("sink")
    net.places.add(source)
    net.places.add(sink)

    for i, sn in enumerate(start_nodes):
        if sn in node_places:
            tau_start = PetriNet.Transition(name=f"tau_start_{sn}_{i}", label=None)
            net.transitions.add(tau_start)
            petri_utils.add_arc_from_to(source, tau_start, net)
            petri_utils.add_arc_from_to(tau_start, node_places[sn]['in'], net)
            
    for i, en in enumerate(end_nodes):
        if en in node_places:
            tau_end = PetriNet.Transition(name=f"tau_end_{en}_{i}", label=None)
            net.transitions.add(tau_end)
            petri_utils.add_arc_from_to(node_places[en]['out'], tau_end, net)
            petri_utils.add_arc_from_to(tau_end, sink, net)

    im = Marking(); im[source] = 1
    fm = Marking(); fm[sink] = 1
    return net, im, fm

def build_optimized_tree(event_log, min_support=5, merge_suffixes=True):
    variants = pm4py.get_variants(event_log)
    dot = graphviz.Digraph(comment='Optimized Tree', format='png')
    trie = {}
    for variant_key, traces_or_count in variants.items():
        count = len(traces_or_count) if isinstance(traces_or_count, list) else traces_or_count
        if count < min_support:
            continue
        activities = [act.strip() for act in variant_key.split(',')] if isinstance(variant_key, str) else variant_key
        current_node = trie
        for activity in activities:
            if activity not in current_node:
                current_node[activity] = {'_count': 0, 'children': {}}
            current_node[activity]['_count'] += count
            current_node = current_node[activity]['children']

    node_id_map = {}; node_counter = [0]; my_nodes = {}; my_edges = []
    my_start_nodes = set(); all_sources = set()

    def draw_recursive(current_dict, parent_id, path_suffix):
        for act, data in current_dict.items():
            suffix_key = f"{act}_{str(list(data['children'].keys()))}" if merge_suffixes else f"{act}_{node_counter[0]}"
            if suffix_key not in node_id_map:
                current_id = f'n{node_counter[0]}'
                node_id_map[suffix_key] = current_id
                node_counter[0] += 1
                my_nodes[current_id] = act
            else:
                current_id = node_id_map[suffix_key]

            if parent_id == 'root':
                my_start_nodes.add(current_id)
            else:
                my_edges.append((parent_id, current_id))
                all_sources.add(parent_id)
            draw_recursive(data['children'], current_id, suffix_key)

    draw_recursive(trie, 'root', 'root')
    my_end_nodes = set(my_nodes.keys()) - all_sources
    return dot, my_nodes, my_edges, list(my_start_nodes), list(my_end_nodes)

# ==========================================
# ΑΝΑΛΥΣΗ ΕΥΑΙΣΘΗΣΙΑΣ
# ==========================================
if __name__ == "__main__":
    file_path = 'BPI_Challenge_2019.xes.gz'
    print("Φόρτωση και φιλτράρισμα...")
    log = pm4py.read_xes(file_path)
    log_filtered = pm4py.filter_variants_top_k(log, 20)
    
    # Οι τιμές support που θα ελέγξουμε
    support_values = [2, 5, 10, 20, 40]
    
    results_fitness = []
    results_precision = []
    results_nodes = []
    
    print("\nΣτήσιμο Πειράματος: Τρέχουμε 5 διαφορετικά Support...")
    print("-" * 65)
    print(f"{'Support':<10} | {'Κόμβοι':<10} | {'Fitness':<12} | {'Precision':<12}")
    print("-" * 65)

    for supp in support_values:
        _, nodes, edges, start_nodes, end_nodes = build_optimized_tree(log_filtered, min_support=supp)
        
        # Αν το support είναι τόσο μεγάλο που σβήνει όλο το γράφημα, το προσπερνάμε
        if len(nodes) == 0:
            print(f"{supp:<10} | {'0':<10} | {'-':<12} | {'-':<12}")
            continue

        net, im, fm = custom_dag_to_petri_net(nodes, edges, start_nodes, end_nodes)
        
        fit = pm4py.fitness_alignments(log_filtered, net, im, fm)['average_trace_fitness']
        prec = pm4py.precision_alignments(log_filtered, net, im, fm)
        
        results_fitness.append(fit)
        results_precision.append(prec)
        results_nodes.append(len(nodes))
        
        print(f"{supp:<10} | {len(nodes):<10} | {fit:<12.4f} | {prec:<12.4f}")

    print("-" * 65)
    
    # --- ΔΗΜΙΟΥΡΓΙΑ ΓΡΑΦΗΜΑΤΟΣ (PLOT) ---
    plt.figure(figsize=(10, 6))
    plt.plot(support_values[:len(results_fitness)], results_fitness, marker='o', linestyle='-', color='blue', label='Fitness')
    plt.plot(support_values[:len(results_precision)], results_precision, marker='s', linestyle='--', color='green', label='Precision')
    
    plt.title('Ανάλυση Ευαισθησίας: Επίδραση του Min Support (BPI 2019)')
    plt.xlabel('Minimum Support (Κατώφλι Κλαδέματος)')
    plt.ylabel('Τιμή Μετρικής (0.0 έως 1.0)')
    plt.ylim(0.5, 1.05)
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend()
    
    # Αποθήκευση της εικόνας
    plt.savefig('sensitivity_analysis_plot.png', dpi=300, bbox_inches='tight')
    print("\n✅ Το γράφημα αποθηκεύτηκε ως 'sensitivity_analysis_plot.png'!")
