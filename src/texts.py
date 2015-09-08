__author__ = 'rainierababao'

"""Does stuff with texts from XML files made by the Go SMS Pro text backup tool.

Complete Sample XML File:
---                                                 ~params~
<GoSms>                                             root (required)
    <SMS>                                           tag per message
        <_id>0001</_id>                             unique message ID
        <address>5125555555</address>               recipient phone number
        <contactName>Foo Bae</contactName>          recipient name
        <date>0123456789123</date>                  POSIX timestamp
        <read>1</read>                              1 if read else 0
        <status>-1</status>                         ??? no clue but they're identical throughout
        <type>1</type>                              1 if received msg else 2
        <reply_path_present>0</reply_path_present>  0 if received msg else None (<reply_path_present/>)
        <body>Hello Rainier</body>                    msg body
        <locked>0</locked>                          1 if text in Go SMS "private box" else 0
    </SMS>
</GoSms>
---
"""

import itertools
import humanhash
import hashlib
import pylab
import csv
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import json
from networkx.readwrite import json_graph
from pandas import read_csv, DataFrame, Series
from indicoio import sentiment_hq, sentiment, named_entities

from lxml import etree
from xml.etree import cElementTree
from time import gmtime, strftime
from collections import Counter, defaultdict

from texts.config import INDICO_API_KEY
from texts.config import TEST_RECIPIENT_A
from texts.config import names
# from texts.config import uvweights

"""Next three functions aren't used in this file explicitly.

They were used to make hard-coded anonymous name pairs in the config file
for O(1) access (previous iteration required XML node traversal)
"""


def digest_and_humanize(word):
    m = hashlib.md5()
    m.update(word)
    return humanhash.humanize(m.hexdigest())


def get_anonymized_names():
    result = dict(zip(get_names(), map(lambda x: digest_and_humanize(x), get_names())))
    # add myself, unanonymized to the anonymized data dict
    result['rainier'] = 'rainier'
    return result


def get_names():
    names = []
    with open('texts/filenames.txt', 'r') as filenames:
        fn_list = map(str.strip, [filename for filename in filenames])
        fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
    for fn in fn_list:
        try:
            tree = cElementTree.parse(fn)
        except cElementTree.ParseError:
            continue
        root = tree.getroot()
        name = root.find('FolderName').text
        names.append(name.lower())
    names.append('rainier')
    return [name for name in map(lambda x: x.split()[0], names) if name.isalpha()]


class TextCorpus(object):
    def __init__(self):
        self.contacts = get_contact_objs()
        self.contact_names = names.values()
        self.global_adj_list_for_nx = [item for sublist in
                                       map(lambda x: getattr(x, 'adjacency_list_for_nx'), self.contacts)
                                       for item in sublist]
        self.global_name_to_pair_set = dict(zip(map(lambda x: getattr(x, 'name'), self.contacts),
                                                map(lambda x: getattr(x, 'adjacency_list_for_nx'),
                                                    self.contacts)))
        self.global_unflattened_pair_set = map(lambda x: getattr(x, 'adjacency_list_for_nx'), self.contacts)


class Contact(object):
    """A Contact obj reprs one of the people I've contacted.
    """

    def __init__(self, fn):
        self.name = get_name_from_fn(fn)
        self.messages = get_texts(fn, False)
        self.messages_as_str_list = map(lambda x: getattr(x, 'body'), self.messages)
        self.links = get_mentions_msg_list(self.messages_as_str_list)
        self.undirected_links = tuple(set(get_mentions_msg_list(self.messages_as_str_list)))
        self.weighted_links = Counter(get_mentions_msg_list(self.messages_as_str_list))
        self.adjacency_list_for_nx = map(lambda x: tuple([self.name, x]),
                                         list(set(get_mentions_msg_list(self.messages_as_str_list))))
        # pass in the dict for num times mentioned and name
        self.sentiment_links = get_sentiment_link_dict(self.weighted_links, self.name)
        self.avg_sentiment = 0.5 if len(self.sentiment_links) is 0 else float(sum(self.sentiment_links.values())) / len(
            self.sentiment_links)


class TextMessage(object):
    """A TextMessage obj's attrs correspond to the XML tags I care about.
    msg_id <- _id.text
    posix <- date.text (POSIX timestamp)
    sent <- True if type.text = 2 else False (True if I sent it else False)
    body <- body.text
    """

    def __init__(self, msg_id, posix, sent, body, sender):
        self.msg_id = msg_id
        self.posix = posix
        self.sent = sent
        self.body = 'neutral' if body is None else anonymize(body.lower())
        self.mentions = get_mentions(self.body)
        # self.sentiment = None # to be read from CSV after the one-off function is called
        self.sender = sender if self.sent is False else 'rainier'


def indico_batch_sentiment():
    """a ONE-OFF method to call the indico.io API to HQ batch sentiment 18192 texts.

    Kinda shows how badly designed OOP code this is right now for the hackathon, oops.
    Should refactor when there is time.
    """
    with open('sentiments.csv', 'wb') as f:
        texts = []
        writer = csv.writer(f)
        with open('texts/filenames.txt', 'r') as filenames:
            fn_list = map(str.strip, [filename for filename in filenames])
            fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
            for fn in fn_list:
                texts.append(get_texts(fn))  # returns TextMessage object
        texts = [item for sublist in texts for item in sublist]
        with open('indico_sentiment_hq_errors.txt', 'w') as error_log:
            for text in texts:
                sentiment_result = None
                try:
                    sentiment_result = sentiment_hq(text.body.encode(), api_key=INDICO_API_KEY)
                except BaseException as e:
                    error_log.write(str(e))
                finally:
                    writer.writerow([unicode(s).encode('utf-8') for s in
                                     [text.msg_id, text.posix, repr(text.sent),
                                      text.body, repr(text.mentions), sentiment_result]])


def indico_batch_ner():
    """another ONE-OFF method to call the indico.io API to batch NER 18192 texts
    """
    with open('sentiments.csv', 'wb') as f:
        texts = []
        writer = csv.writer(f)
        with open('texts/filenames.txt', 'r') as filenames:
            fn_list = map(str.strip, [filename for filename in filenames])
            fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
            for fn in fn_list:
                texts.append(get_texts(fn))  # returns TextMessage object
        texts = [item for sublist in texts for item in sublist]
        with open('indico_ner_errors.txt', 'w') as error_log:
            for text in texts:
                sentiment_result = None
                try:
                    sentiment_result = named_entities(text.body.encode(), api_key=INDICO_API_KEY)
                except BaseException as e:
                    error_log.write(str(e))
                finally:
                    writer.writerow([unicode(s).encode('utf-8') for s in
                                     [text.msg_id, text.posix, repr(text.sent),
                                      text.body, repr(text.mentions), sentiment_result]])


def get_uvweights():
    uvweights = []
    for contact in get_contact_objs():
        for k, v in contact.sentiment_links.iteritems():
            uvweights.append((contact.name, k, v))
    # print uvweights
    return uvweights


def nx_graph():
    """Make graph using networkx lib. Prints to matplotlib window and saves png in working dir.
    """
    adj_list = TextCorpus().global_adj_list_for_nx
    print adj_list
    G = nx.Graph()
    G.add_edges_from(adj_list)
    nx.draw(G)
    img_fn = "graph-{0}".format(strftime('%Y-%m-%d %H:%M:%S.png', gmtime()))
    plt.savefig(img_fn)
    plt.show()


def nx_graph_freq_weighted():
    """Make graph with state indication between nodes.
    """
    adj_list = TextCorpus().global_adj_list_for_nx
    print '-- Adjacency List --\n{0}'.format(adj_list)
    G = nx.Graph()
    pos = nx.spring_layout(G)
    # nx.draw_networkx_nodes(G, pos, nodelist=[contact for contact in get_contact_objs() if contact.avg_sentiment < 0.33],
    #                       node_color='r', node_size=300, alpha=0.8)
    # nx.draw_networkx_nodes(G, pos, nodelist=[contact for contact in get_contact_objs() if 0.33 < contact.avg_sentiment && contact.avg_sentiment < 0.66],
    #                         node_color='y', node_size=300, alpha=0.8)
    # nx.draw_networkx_nodes(G, pos, nodelist=[contact for contact in get_contact_objs() if 0.66 < contact.avg_sentiment && contact.avg_sentiment < 0.80],
    #                         node_color='c', node_size=300, alpha=0.8)
    # nx.draw_networkx_nodes(G, pos, nodelist=[contact for contact in get_contact_objs() if 0.80 < contact.avg_sentiment],
    #                         node_color='m', node_size=300, alpha=0.8)
    # nx.draw_networkx_edges(G, pos, width = 1.0, alpha = 0.5)
    # nx.draw_networkx_edges(G, pos, edgelist=adj_list, width=(8), )


    G.add_edges_from(adj_list)
    G = nx.MultiGraph(G)
    G.add_weighted_edges_from(get_uvweights())
    nx.draw_shell(G)
    img_fn = "w_graph-{0}".format(strftime('%Y-%m-%d %H:%M:%S.png', gmtime()))
    plt.savefig(img_fn)
    plt.show()


def nx_graph_freq_state():
    """Better.
    """
    adj_list = TextCorpus().global_adj_list_for_nx
    G = nx.Graph()
    G.add_edges_from(adj_list)
    pos = nx.spring_layout(G)
    pylab.figure(2)
    nx.draw(G, pos)
    node_labels = nx.get_node_attributes(G, 'state')
    nx.draw_networkx_labels(G, pos, labels=node_labels)
    edge_labels = nx.get_edge_attributes(G, 'state')
    nx.draw_networkx_edge_labels(G, pos, labels=edge_labels)
    img_fn = "f_graph-{0}".format(strftime('%Y-%m-%d %H:%M:%S.png', gmtime()))
    plt.savefig(img_fn)
    plt.show()


def nx_graph_json():
    adj_list = TextCorpus().global_adj_list_for_nx
    G = nx.Graph()
    G.add_edges_from(adj_list)
    data = json_graph.node_link_data(G)
    s = json.dumps(data, sort_keys=True, indent=4)
    return s


def get_sentiment_link_dict(link_freq, name):
    df = pd.read_csv('sentiments_fixed.csv')
    sent_msg_df = df[df['sender'] == name]
    dict_of_mentioned = defaultdict(float)
    for index, row in sent_msg_df.iterrows():
        mentioned = eval(row[0])
        if len(mentioned) > 0:
            for mention in mentioned:
                # print row[1], type(row[1])
                if row[1] is None or row[1] == 'None' or row[1] is 'None':
                    continue
                else:
                    dict_of_mentioned[mention] += float(row[1].strip('"').strip("'"))
    # average the total
    for mention in dict_of_mentioned:
        dict_of_mentioned[mention] = float(dict_of_mentioned[mention]) / link_freq[mention]
    return dict_of_mentioned


def get_contact_objs():
    """Get all of the Contact objects.
    """
    contacts = []
    with open('texts/filenames.txt', 'r') as filenames:
        fn_list = map(str.strip, [filename for filename in filenames])
        fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
    for fn in fn_list:
        contacts.append(Contact(fn))
    return contacts


def fix_sentiments():
    """Add the 'sender' column so I know who to make a connection to.
    """
    df = DataFrame.from_csv('sentiments.csv')
    texts = []
    with open('texts/filenames.txt', 'r') as filenames:
        fn_list = map(str.strip, [filename for filename in filenames])
        fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
        for fn in fn_list:
            texts.append(get_texts(fn))  # returns TextMessage object
    texts = map(lambda x: getattr(x, 'sender'), [item for sublist in texts for item in sublist])
    df['sender'] = Series(texts, index=df.index)
    df.to_csv('sentiments_fixed.csv', encoding='utf-8')


def anonymize_msg_list(msg_list):
    """Anonymize a list of text bodies.
    """
    for i in range(len(msg_list)):
        for orig, hmhashed in names.iteritems():
            msg_list[i] = msg_list[i].replace(orig, hmhashed)
    return msg_list


def anonymize(msg):
    """Anonymize a single text body.
    """
    for orig, hmhashed in names.iteritems():
        msg = msg.replace(orig, hmhashed)
    return msg


def pretty_print_xml_to_file(orig_fn, new_fn=None):
    """Converts unformatted XML file to new pretty print XML file.

    Required <orig_fn> param (str) to get XML filepath
    Optional <new_fn> param (str) to get new XML filepath
    If default (None), then the new file will be called 'pretty_<orig_fn>.xml'
    """
    if new_fn is None:
        new_fn = 'texts/pretty_{0}'.format(orig_fn.split('/')[1])
    x = etree.parse(orig_fn)
    with open(new_fn, 'w') as f:
        xml_as_str = etree.tostring(x, pretty_print=True)
        f.write(xml_as_str)
    y = etree.parse(new_fn)
    return y


def get_mentions_msg_list(msg_list):
    mentions = []
    for msg in msg_list:
        for orig, hmhashed in names.iteritems():
            if hmhashed in msg:
                mentions.append(hmhashed)
    return mentions


def get_mentions(msg):
    mentions = []
    for orig, hmhashed in names.iteritems():
        if hmhashed in msg:
            mentions.append(hmhashed)
    return mentions


def get_name_from_fn(fn):
    tree = cElementTree.parse(fn)
    root = tree.getroot()
    name = root.find('FolderName').text
    return names[name.lower().split()[0]]


def get_texts(orig_fn, get_sent=None):
    """Get a list of TextMessage objects.

    Because of how the data was represented in the XML,
    TextMessages are already sorted by their <posix> attr.

    Required <orig_fn> param (str) to get XML filepath
    Optional <get_sent> param (bool) to get texts I sent vs. texts I received
    If default (None), then all texts are retrieved.
    """
    tree = cElementTree.parse(orig_fn)
    root = tree.getroot()
    sender = names[root.find('FolderName').text.lower().split()[0]]
    msg_nodes = [child for child in root if child.tag == 'SMS']
    msg_ids, posixs, sents, bodys = [], [], [], []
    for msg in msg_nodes:
        for tag in msg:
            if tag.tag == '_id':
                msg_ids.append(tag.text)
            elif tag.tag == 'date':
                posixs.append(tag.text)
            elif tag.tag == 'type':
                sents.append(True if tag.text == '2' else False)
            elif tag.tag == 'body':
                bodys.append(tag.text)
    texts = []
    for msg_id, posix, sent, body in itertools.izip(msg_ids, posixs, sents, bodys):
        texts.append(TextMessage(msg_id, posix, sent, body, sender))
    if get_sent is None:
        return texts
    else:
        my_texts, their_texts = [], []
        for text in texts:
            if text.sent:
                my_texts.append(text)
            else:
                their_texts.append(text)
        if get_sent:
            return my_texts
        else:
            return their_texts


def get_num_texts_in_corpus_soft():
    """Returns the number of texts in the texts/texts folder,
    based on the value of the SMSCount node.
    """
    total = 0
    with open('texts/filenames.txt', 'r') as filenames:
        fn_list = map(str.strip, [filename for filename in filenames])
        fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
    for fn in fn_list:
        try:
            tree = cElementTree.parse(fn)
        except cElementTree.ParseError:
            continue
        root = tree.getroot()
        total += eval(root.find('SMSCount').text)
    return total


def get_num_texts_in_corpus_hard():
    """Returns the number of texts in the texts/texts folder,
    based on the number of text body nodes.
    """
    total = 0
    with open('texts/filenames.txt', 'r') as filenames:
        fn_list = map(str.strip, [filename for filename in filenames])
        fn_list = map(lambda x: 'texts/texts/' + x, fn_list)
    for fn in fn_list:
        total += len(get_texts(fn))
    return total


if __name__ == '__main__':
    foo = TextCorpus()
    print foo.global_unflattened_pair_set
    # get_uvweights()
    # nx_graph_freq_weighted()
    # print nx_graph_json()
    # nx_graph()
    # Sanity checks.
    # print get_num_texts_in_corpus_soft()
    # print get_num_texts_in_corpus_hard()
