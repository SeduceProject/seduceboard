
# The states
user_initial_state = 'created'
user_states = [user_initial_state, 'waiting_confirmation_email', 'confirmed', 'waiting_authorization', 'authorized',
                'unauthorized']

# And some transitions between states.
user_transitions = [
    {'trigger': 'email_sent', 'source': user_initial_state, 'dest': 'waiting_confirmation_email'},
    {'trigger': 'confirm_email', 'source': 'waiting_confirmation_email', 'dest': 'confirmed'},
    {'trigger': 'notify_admin', 'source': 'confirmed', 'dest': 'waiting_authorization'},
    {'trigger': 'approve', 'source': 'waiting_authorization', 'dest': 'authorized'},
    {'trigger': 'disapprove', 'source': 'waiting_authorization', 'dest': 'unauthorized'},
    {'trigger': 'deauthorize', 'source': 'authorized', 'dest': 'unauthorized'},
    {'trigger': 'reauthorize', 'source': 'unauthorized', 'dest': 'authorized'},
]

# The states
cq_initial_state = 'created'
cq_states = [cq_initial_state, 'running', 'waiting', 'finished']

# And some transitions between states.
cq_transitions = [
    {'trigger': 'run', 'source': [cq_initial_state, "waiting"], 'dest': 'running'},
    {'trigger': 'wait', 'source': 'running', 'dest': 'waiting'},
    {'trigger': 'finish', 'source': 'waiting', 'dest': 'finished'},
]
