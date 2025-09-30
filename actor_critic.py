import torch
from torch import nn
from torch.distributions import Categorical


def init_weights(m):
    if isinstance(m, nn.Linear):
        nn.init.normal_(m.weight, mean=0.0, std=0.1)
        # nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
        nn.init.constant_(m.bias, 0.1)


class ActorCritic(nn.Module):
    def __init__(self, num_inputs, num_outputs, shared_sizes, critic_sizes, actor_sizes):
        super(ActorCritic, self).__init__()

        self.num_outputs = num_outputs

        # Shared network
        shared_sizes.insert(0, num_inputs)
        last_size = shared_sizes[0]
        shared_layers = []

        for size in shared_sizes[1:]:
            shared_layers += [
                nn.Linear(last_size, size),
                nn.ReLU(),
            ]
            last_size = size
        shared_last_size = last_size

        self.shared = nn.Sequential(*shared_layers)

        # Critic network
        critic_sizes.insert(0, shared_last_size)
        last_size = critic_sizes[0]
        critic_layers = []

        for size in critic_sizes[1:]:
            critic_layers += [
                nn.Linear(last_size, size),
                nn.ReLU(),
            ]
            last_size = size
        critic_layers += [
            nn.Linear(last_size, 1),
        ]

        self.critic = nn.Sequential(*critic_layers)

        # Actor network
        actor_sizes.insert(0, shared_last_size)
        last_size = actor_sizes[0]
        actor_layers = []

        for size in actor_sizes[1:]:
            actor_layers += [
                nn.Linear(last_size, size),
                nn.ReLU(),
            ]
            last_size = size
        actor_layers += [
            nn.Linear(last_size, num_outputs),
        ]

        self.actor = nn.Sequential(*actor_layers)

        self.apply(init_weights)

    def forward(self, x):
        intermediate = self.shared(x)
        value = self.critic(intermediate)
        actions_logits = self.actor(intermediate)
        dist = Categorical(logits=actions_logits)
        return dist, value
