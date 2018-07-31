# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 10:17:43 2018

@author: Alok
Title : Create a Cryptocurrency
"""
# -*- coding: utf-8 -*-
#requests==2.18.4 pip install 

#Import the libraries
import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests 
from uuid import uuid4
from urllib.parse import urlparse

#Part 1 - Building a blockchain
class Blockchain:
    
    def __init__(self):
        self.chain=[]
        self.trasactions=[];
        self.create_block(proof=1,previous_hash='0')
        self.nodes=set()
        
    
    def create_block(self,proof,previous_hash):
        block={
                'index':len(self.chain)+1,
                'timestamp':str(datetime.datetime.now()),
                'proof':proof,
                'previous_hash':previous_hash,
                'transactions':self.trasactions
                }
        self.trasactions=[]
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            hash_operation=hashlib.sha256(str(new_proof**2 - previous_proof**2).encode() ).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof=True
            else:
                new_proof+=1
        
        return new_proof

    def hash(self,block):
        encoded_block=json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        block_index=1
        while block_index < len(chain):
            block=chain[block_index]
            if self.hash(previous_block)!=block['previous_hash']:
                return False
            previous_proof=previous_block['proof']
            proof=block['proof']
            hash_operation=hashlib.sha256(str(proof**2 - previous_proof**2).encode() ).hexdigest()
            if hash_operation[:4]!='0000':
                return False
            previous_block=block
            block_index+=1
        return True
    
    def addTrasanction(self,sender,receiver,amount):
        self.trasactions.append({'sender':sender,'receiver':receiver,'amount':amount})
        previous_block=self.get_previous_block()
        return previous_block['index']+1
    
    def addNode(self,address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replaceChain(self):
        network=self.nodes
        longest_chain=None
        max_length=len(self.chain)
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code==200:
                length=response.json()['length']
                chain=response.json()['chain']
                if length> max_length and self.is_chain_valid(chain):
                    max_length=length
                    longest_chain=chain
        
        if longest_chain:
            self.chain=longest_chain
            return True
        return False
#Part 2 - Mining our Blockchain
        
app=Flask(__name__)

#Creating an address for the node on Port 5000
node_address=str(uuid4()).replace('-','')


blockchain=Blockchain()
    
@app.route('/mine_block',methods=['GET'])
def mine_block():
        previous_block=blockchain.get_previous_block()
        previous_proof=previous_block['proof']
        proof=blockchain.proof_of_work(previous_proof)
        previous_hash=blockchain.hash(previous_block)
        blockchain.addTrasanction(sender=node_address,receiver='Hadnan',amount=10)
        block=blockchain.create_block(proof,previous_hash)
        response={
                  'message':'Congratulations, you just mined a block!',
                  'index':block['index'],
                  'timestamp':block['timestamp'],
                  'proof':block['proof'],
                  'previous_hash':block['previous_hash'],
                  'transactions':block['transactions']
                  }
        return jsonify(response),200
    
    
#Getting the full blockchain
@app.route('/get_chain',methods=['GET'])
def get_chain():
    response={'chain':blockchain.chain,
              'length':len(blockchain.chain)}
    return jsonify(response),200

#check if blockchain is valid or not
@app.route('/is_valid',methods=['GET'])
def is_valid():
    is_valid=blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response={'message':'All good!! Blockchain is valid'}
    else:
        response={'message':'Blockchain is not valid'}
    return jsonify(response),200

#to add a transaction
@app.route('/add_transactions',methods=['POST'])
def add_transaction():
    json=request.get_json()
    transaction_keys=['sender','receiver','amount']
    if not all  (key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing',400
    index = blockchain.addTrasanction(json['sender'],json['receiver'],json['amount'])
    response= {'message':f'This transaction will be added to Block {index}'}
    return jsonify(response),201

#Decentralising our Blockchain

#Connecting new nodes
@app.route('/connect_node',methods=['POST'])
def connect_node():
    json=request.get_json()
    nodes=json.get('nodes')
    if nodes is None:
        return 'No node',400
    for node in nodes:
        blockchain.addNode(node)
    response={'message':'All the nodes are now connected. The Hadcoin Blockchain now contains the following number of nodes','total_nodes':list(blockchain.nodes)}
    return jsonify(response),201

#Replcaing the chain by the longest chain if needed
@app.route('/replace_chain',methods=['GET'])
def replace_chain():
    is_chain_replaced=blockchain.replace_chain()
    if is_chain_replaced:
        response={'message':'Nodes have different chains!! Chain replaced',
                  'new_chain':blockchain.chain}
    else:
        response={'message':'All good!! Chain is the longest one',
                  'actual_chain':blockchain.chain}
    return jsonify(response),200 

#Running the app through flask
app.run(host='0.0.0.0',port=5001)

