import argparse

def get_parser_nmt():
	parser = argparse.ArgumentParser()

	parser.add_argument('--batch-size', action='store', dest='batch_size',help='batch-size , default 64',type=int,default = 64)

	parser.add_argument('--epochs', action='store', dest='n_epochs',help='# of epochs, default = 1000',type=int,default = 1000)

	parser.add_argument('--patience', action='store', dest='patience',help='# of epochs for patience, default = 20',type=int,default = 20)

	parser.add_argument('--dropout', action='store', dest='dropout',help='# of epochs for patience, default = 0.0',type=float,default = 0.0)

	parser.add_argument('--unit', action='store', dest='unit',help='train with {lstm gru rnn} units,default = lstm', default = 'lstm')

	parser.add_argument('--hidden', action='store', dest='n_hidden',help='hidden size of neural networks, default = 256',type=int,default = 256)

	parser.add_argument('--layers', action='store', dest='layers',help='# of layers, default = 1',type=int,default = 1)

	parser.add_argument('--model', action='store', dest='model',help='model type {0 , 1 , 2}, default = 0',type=int, default = 0)

	parser.add_argument('--prefix', action='store', dest='prefix',help='exp log prefix to append exp/{} default = 0',default = '0')

	parser.add_argument('--source', action='store', dest='source',help='source file for validation default = ../data/val.de.task1',default = '../data/val.de.')

	parser.add_argument('--use-hierarchical', action='store_true', dest='hierarchical',help='use hierarchical softmax, default : true')

	parser.add_argument('--suffix', action='store', dest='suffix',help='full|task1|debug data, default = task1',default = 'task1')

	parser.add_argument('--filter-mode', action='store', dest='filter_mode',help='filter mode = 0',type=int,default = 0)

	parser.add_argument('--dropmodality', action='store_true', dest='dropmodality',help='use dropmodality, default : false')

	parser.set_defaults(hierarchical = True)

	parser.set_defaults(dropmodality = False)

	return parser

def get_parser_nmt_test():
	parser = argparse.ArgumentParser()

	parser.add_argument('--suffix', action='store', dest='suffix',help='full|task1|debug data, default = task1',default = 'task1')
	parser.add_argument('--path', action='store', dest='path',help='<model_name> path where <model_name>.{meta|model|arch} exist',default = '')
	parser.add_argument('--samples', action='store', dest='samples',help='# of samples 0 : for all, default 0', type = int, default = 0)
	parser.add_argument('--mtype', action='store', dest='m_type',help='model type {text|text+image|image} ',default = '')
	parser.add_argument('--func', action='store', dest='func',help='function type {test|error|eval} ',default = 'eval')
	parser.add_argument('--filter-mode', action='store', dest='filter_mode',help='filter mode = 0',type=int,default = 0)
	parser.add_argument('--cnn-filter-file', action='store', dest='cnn_filter_file',help='cnn filter file default = ""',default = '')

	return parser

def get_embeddings(word_idx, idx_word, wvec = '../embeddings/word2vec.pkl', UNK_vmap = '*UNKNOWN*', expand_vocab = False):
	import gzip, sys
	import cPickle as pickle
	import numpy as np

	try:
		print >> sys.stderr, "loading word vectors..."
		v_map = pickle.load(gzip.open(wvec, "rb"))
		dim = len(list(v_map[UNK_vmap]))
		print >> sys.stderr, "%d dim word vectors are loaded.." % (dim)
	except:
		print >> sys.stderr, "word embedding file %s cannot be read." % (wvec)
		quit(1)

	V_text = len(word_idx)

	if expand_vocab:
		for w in v_map.keys():
			if w not in word_idx:
				V_text += 1
				word_idx[w] = V_text
				idx_word[V_text] = w

	embedding_weights = np.zeros((V_text+1,dim))

	for w in word_idx:
		idx = word_idx[w]
		if w not in v_map:
			w = UNK_vmap
		try:
			embedding_weights[idx,:] = v_map[w]
		except:
			print >> sys.stderr, "something is wrong with following tuple:", idx, idx_word[idx], w
			quit(1)
	return embedding_weights, word_idx, idx_word


def decode_predicted(fname, predicted, dicts, HIERARCHICAL = True):
	import numpy as np
	import sys

	f = open(fname, 'w')
	V_de = len(dicts['word_idx_de'])
	dim = int(pow(V_de,0.25)) + 1
	vocab = range(V_de)
	S = []
	EOS = dicts['word_idx_de']['</s>']
	print >> sys.stderr, "decoding prediction..."
#	print >> sys.stderr, "debug-->", predicted['output_1'].shape
	for i in xrange(predicted['output_1'].shape[0]):
		if HIERARCHICAL:
			probabilities = []
			for j in xrange(predicted['output_1'].shape[1]):
				prob_token = np.zeros((V_de,1))

				tmp1 = np.outer(predicted['output_1'][i,j],predicted['output_2'][i,j]).flatten()
				tmp2 = np.outer(predicted['output_3'][i,j],predicted['output_4'][i,j]).flatten()
				outer1 = np.outer(tmp1,tmp2).flatten()
				prob_token = outer1[:V_de].reshape((1,V_de))
				probabilities += [ prob_token/ np.sum(prob_token)]
		else:
			probabilities = predicted['output'][i]

		greedy = [ np.argmax(p) for p in probabilities]
		greedy_probs = [ np.max(p) for p in probabilities]
		try:
			greedy_clipped = greedy[:greedy.index(EOS)]
		except:
			greedy_clipped = greedy
			pass
#		print >> sys.stderr, "-->", greedy
		seq = [ dicts['idx_word_de'][idx] for idx in greedy_clipped]
		print >> f, " ".join(seq)
	f.close()
	print >> sys.stderr, "decoding done."
