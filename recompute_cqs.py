from core.data.cq_aggregates import cqs_recreate_all
from core.data.cq_aggregates import cqs_recompute_data
from core.data.cq_aggregates import cq_multitree_recreate_all

if __name__ == "__main__":
    # Will recompute data of continuous queries
    print("I will recompute data of continuous queries")
    print("  - cqs_recreate_all")
    # cqs_recreate_all(force_creation=True)
    print("  - cqs_recompute_data")
    # cqs_recompute_data()
    print("  - cq_multitree_recreate_all")
    cq_multitree_recreate_all(True)
    cq_multitree_recreate_all(False)
