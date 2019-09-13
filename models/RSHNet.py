import torch as t
import torch.nn as nn

class RSHNet(nn.Module):
	'''
		Recurrent Selective Hearing Networks

		Reference:
			Kinoshita K, Drude L, Delcroix M, et al. Listening to Each Speaker One by One with Recurrent Selective Hearing Networks[C]. international conference on acoustics, speech, and signal processing, 2018: 5064-5068.
	'''
	def __init__(self, num_bins=129,
			rnn="lstm",
			num_layers=2,
			hidden_size=600,
			act_func="sigmoid",
			bidirectional=True):
		super(RSHNet, self).__init__()
		self.name = "RSHNet"
		if act_func not in ["tanh", "sigmoid"]:
			raise ValueError("Unsupported activation function type:{}".format(act_func))

		rnn = rnn.upper()
		if rnn not in ["RNN", "GRU", "LSTM"]:
			raise ValueError("Unsupported rnn type:{}".format(rnn))

		self.rnn = getattr(nn, rnn)(
			num_bins * 2,
			hidden_size,
			num_layers,
			batch_first=True,
			bidirectional=bidirectional
		)

		self.mask = nn.Linear(
			hidden_size * 2 if bidirectional else hidden_size,
			num_bins
		)

		self.act_func = {
			"sigmoid":t.sigmoid,
			"tanh":t.tanh}[act_func]

		self.flag = nn.Linear(hidden_size * 2 if bidirectional else hidden_size, 1)

	def forward(self, x, C):
		'''
			input:
				x [B, T, num_bins] concate with M [B, T, num_bins]
				C scalar
			output:
				M_ [C + 1, B, T, num_bins] and flags z [z_1, ..., z_C]
		'''
		if x.dim() != 3:
			x = t.unsqueeze(x, 0)

		Ms = []
		zs = []

		M = t.ones(x.shape)

		for i in range(C):
			y = t.cat([x, M], dim=-1)
			y, _ = self.rnn(y)	# y: [B, T, hidden_size * 2]
			m = self.mask(y) # m: [B, T, num_bins]
			m = self.act_func(m)
			Ms.append(m)
			M -= m
			z = self.flag(y)
			z = t.mean(t.sigmoid(z).squeeze(2), 1)
			zs.append(z)

		Ms.append(M)
		return Ms, zs