
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.8'

_lr_method = 'LALR'

_lr_signature = '9195A5F7E05E627AC0F404F95AEB41BA'
    
_lr_action_items = {'/':([2,4,6,11,12,13,15,16,17,18,19,20,],[7,-9,-10,7,-10,-7,-6,7,-5,7,-8,7,]),'NUMBER':([0,3,5,7,8,9,10,14,],[4,4,4,4,4,4,4,4,]),')':([4,11,12,13,15,16,17,18,19,],[-9,19,-10,-7,-6,-3,-5,-4,-8,]),'-':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,],[5,10,5,-9,5,-10,5,5,5,5,10,-10,-7,5,-6,-3,-5,-4,-8,10,]),'(':([0,3,5,7,8,9,10,14,],[3,3,3,3,3,3,3,3,]),'*':([2,4,6,11,12,13,15,16,17,18,19,20,],[9,-9,-10,9,-10,-7,-6,9,-5,9,-8,9,]),'+':([2,4,6,11,12,13,15,16,17,18,19,20,],[8,-9,-10,8,-10,-7,-6,-3,-5,-4,-8,8,]),'$end':([1,2,4,6,12,13,15,16,17,18,19,20,],[0,-2,-9,-10,-10,-7,-6,-3,-5,-4,-8,-1,]),'=':([6,],[14,]),'NAME':([0,3,5,7,8,9,10,14,],[6,12,12,12,12,12,12,12,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'statement':([0,],[1,]),'expression':([0,3,5,7,8,9,10,14,],[2,11,13,15,16,17,18,20,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> statement","S'",1,None,None,None),
  ('statement -> NAME = expression','statement',3,'p_statement_assign','valueInterpret.py',50),
  ('statement -> expression','statement',1,'p_statement_expr','valueInterpret.py',54),
  ('expression -> expression + expression','expression',3,'p_expression_binop','valueInterpret.py',59),
  ('expression -> expression - expression','expression',3,'p_expression_binop','valueInterpret.py',60),
  ('expression -> expression * expression','expression',3,'p_expression_binop','valueInterpret.py',61),
  ('expression -> expression / expression','expression',3,'p_expression_binop','valueInterpret.py',62),
  ('expression -> - expression','expression',2,'p_expression_uminus','valueInterpret.py',69),
  ('expression -> ( expression )','expression',3,'p_expression_group','valueInterpret.py',73),
  ('expression -> NUMBER','expression',1,'p_expression_number','valueInterpret.py',77),
  ('expression -> NAME','expression',1,'p_expression_name','valueInterpret.py',81),
]
