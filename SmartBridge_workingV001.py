from copy import deepcopy
import maya.cmds as cmds
import pymel.core as pm
from functools import partial

class Demand():
	dmd_verts=0
	dmds_list=[]

tempStorage={
	'optionNo':1
}
dstTempDict={}

def subset_sum(numbers, target, partial=[]):
	s = 0
	for value in partial:
		s += (value-1)
	if s == target:
		optionNoVar=tempStorage['optionNo']
		tempStorage[optionNoVar]=partial
		optionNoVar+=1
		tempStorage['optionNo']=optionNoVar
	if s >= target:
		return

	for i in range(len(numbers)):
		remaining = []
		n = numbers[i]
		remaining.append(n)
		for j in range(i+1, len(numbers), 1):
			remaining.append(numbers[j])
		subset_sum(remaining, target, partial + [n])

def vertsDstSort(vtx):
	return dstTempDict[vtx]

def locsToSide(sideAB, sideVertsList, *args):
	if smartBridgeDict['main_mesh'] == 'nomesh':
		meshSplit=sideVertsList[0].split('.')
		smartBridgeDict['main_mesh']=meshSplit[0]
	sideVertsAmt=len(sideVertsList)
	fstSelVertLoc=cmds.pointPosition(smartBridgeDict[sideAB]['fstVtx'])
	for selVtx in sideVertsList:
		crtSelVertLoc=cmds.pointPosition(selVtx)
		newDstCreate=cmds.distanceDimension( sp=(fstSelVertLoc[0], fstSelVertLoc[1], fstSelVertLoc[2]), ep=(crtSelVertLoc[0], crtSelVertLoc[1], crtSelVertLoc[2]))
		cmds.select(newDstCreate, hierarchy=True)
		couldBeDstDimShape=cmds.ls(sl=True, fl=True)
		for couldBe in couldBeDstDimShape:
			couldBeAttr=cmds.listAttr(couldBe)
			if 'distance' in couldBeAttr:
				newDst=cmds.getAttr(couldBe+'.distance')
				dstTempDict[selVtx]=newDst
				dispLoc1=cmds.listConnections(couldBe+'.endPoint')
				dispLoc2=cmds.listConnections(couldBe+'.startPoint')
				cmds.delete(dispLoc1, dispLoc2, couldBeDstDimShape)
	sideVertsList.sort(key=vertsDstSort) 
	print(dstTempDict)
	print(sideVertsList)

	locNo=0
	cmds.group(em=True, name=sideAB+'_grp')
	for sideVert in sideVertsList:
		locNo+=1
		spaceLoc=sideAB+'_'+str(locNo)+'_loc'
		cmds.spaceLocator(name=spaceLoc)
		sideVertLoc=cmds.pointPosition(sideVert)
		cmds.setAttr(spaceLoc+'.translateX', sideVertLoc[0])
		cmds.setAttr(spaceLoc+'.translateY', sideVertLoc[1])
		cmds.setAttr(spaceLoc+'.translateZ', sideVertLoc[2])
		cmds.parent(spaceLoc, sideAB+'_grp')
	smartBridgeDict[sideAB]['vertsNo']=locNo
	pm.mel.dR_DoCmd("modeObject")
	cmds.select(clear=True)

def pickAsFstVtx(sideAB,*args):
	fstVtx=cmds.ls(sl=True, fl=True)
	if fstVtx[0] in smartBridgeDict[sideAB]['all_verts']:
		smartBridgeDict[sideAB]['fstVtx']=fstVtx
	else:
		print('not in side storage')

def storeSide(sideAB, *args):
	cmds.ConvertSelectionToVertices()
	allSideVerts=cmds.ls(sl=True, fl=True)
	smartBridgeDict[sideAB]['all_verts']=allSideVerts
	print(sideAB)
	print(smartBridgeDict[sideAB]['all_verts'])

def startBridge(invSdBChk, *argh):
	for sideAB in ['sideA', 'sideB']:
		sideVertsList=smartBridgeDict[sideAB]['all_verts']
		locsToSide(sideAB, sideVertsList)

	for sideAB in ['sideA', 'sideB']:
		target = smartBridgeDict[sideAB]['vertsNo']
		print("Target = " + str(target))
		if target < 100:
			subset_sum([2, 3, 4, 5], target-1)
			smartBridgeDict[sideAB]['options']=deepcopy(tempStorage)
			del smartBridgeDict[sideAB]['options']['optionNo']
			tempStorage.clear()
			tempStorage['optionNo']=1
			smartBridgeDict[sideAB]['demands']={}
			for k0, v0 in smartBridgeDict[sideAB]['options'].items():
				dmdVerts=1
				dmdsList=[]
				for nest in v0:
					demand=smartBridgeDict['dmdsSwitch'][str(nest)]
					dmdsList.append(demand)
					dmdVerts+= (demand-1)
				newDmd=Demand()
				newDmd.dmd_verts=dmdVerts
				newDmd.dmds_list=deepcopy(dmdsList)
				smartBridgeDict[sideAB]['demands'][k0]=newDmd

	foundMatch=False
	for k0, v0 in smartBridgeDict['sideA']['demands'].items():
		if v0.dmd_verts == smartBridgeDict['sideB']['vertsNo']:
			foundMatch=True
			print('found match for option '+str(k0)+' on sideB')
			print(str(v0.dmd_verts)+' verts demanded')
			print('demands list '+str(v0.dmds_list))
			smartBridgeDict['locs']={}
			for sideAB in ['sideA', 'sideB']:
				for loc in cmds.ls(type='transform'):
					if sideAB in loc and '_loc' in loc:
						transXYZ=[]
						smartBridgeDict['locs'][loc]={}
						for ltr in 'XYZ':
							newVal=cmds.getAttr(loc+'.translate'+ltr)
							smartBridgeDict['locs'][loc][ltr]=newVal
					elif 'distanceDimension' in loc:
						cmds.delete(loc)
			cmds.group(em=True, name='bridgePolys_grp')
			planBridge(k0, v0)
			break
	if foundMatch == False:
		cmds.window(widthHeight=(200, 100))
		cmds.columnLayout(width=190)
		cmds.text(label='SmartBridge does not give the best results with circles or other closed edgeloops, if both sides are open edgeloops try adding or removing an edgeloop on one of the sides and reload the tool', width=190, ww=True)
		cmds.setParent('..')
		cmds.showWindow()
		cmds.delete('sideA_grp', 'sideB_grp')

def planBridge(dmdKey, dmdObj):
	sdAlocNo=1
	sdAnestVertsList=[]
	sdBlocNo=1
	sdBnestVertsList=[]
	vertsSetKey=0
	for vertsSet in smartBridgeDict['sideA']['options'][dmdKey]:
		print('dmdKey:'+str(dmdKey))
		vertsSetKey+=1
		sdAnestVertsList.append('sideA_'+str(sdAlocNo)+'_loc')
		for n in range(vertsSet-1):
			sdAlocNo+=1
			sdAnestVertsList.append('sideA_'+str(sdAlocNo)+'_loc')
			print('n '+str(n)+', sdAlocNo '+str(sdAlocNo)+', sdAnestVertsList '+str(sdAnestVertsList))
		setDmd=smartBridgeDict['dmdsSwitch'][str(vertsSet)]
		sdBnestVertsList.append('sideB_'+str(sdBlocNo)+'_loc')
		for m in range(setDmd-1):
			sdBlocNo+=1
			sdBnestVertsList.append('sideB_'+str(sdBlocNo)+'_loc')
			print('m '+str(m)+', sdBlocNo '+str(sdBlocNo)+', sdBnestVertsList '+str(sdBnestVertsList))
		smartBridgeDict['nests'][str(vertsSetKey)]={}
		smartBridgeDict['nests'][str(vertsSetKey)]['sideA']=deepcopy(sdAnestVertsList)
		smartBridgeDict['nests'][str(vertsSetKey)]['sideB']=deepcopy(sdBnestVertsList)
		smartBridgeDict['nests'][str(vertsSetKey)]['blueprint_type']=vertsSet
		del sdAnestVertsList[:]
		del sdBnestVertsList[:]
	print(smartBridgeDict['nests'])
	for k0, v0 in smartBridgeDict['nests'].items():
		if v0['blueprint_type']==2:
			planTwoNest(k0, v0)
		if v0['blueprint_type']==3:
			planFiveNest(k0, v0, 'sideB', 'sideA')
		if v0['blueprint_type']==4:
			planFourNest(k0, v0, 'sideA', 'sideB')
		if v0['blueprint_type']==5:
			planFiveNest(k0, v0, 'sideA', 'sideB')
	cmds.delete('sideA_grp', 'sideB_grp')
	cmds.select(smartBridgeDict['main_mesh'], 'bridgePolys_grp')
	cmds.CombinePolygons()
	meshToBlank=cmds.ls(sl=True, type='transform')
	smartBridgeDict['main_mesh']=meshToBlank
	cmds.PolyMerge()
	cmds.ConformPolygonNormals()
	pm.mel.dR_DoCmd("modeObject")
	cmds.delete (meshToBlank, ch=True)
	cmds.makeIdentity(meshToBlank, apply=True, t=1, r=1, s=1, n=0)
	cmds.select(clear=True)

def buildPoly(polyName, polyVtx1, polyVtx2, polyVtx3, polyVtx4):
	print('attempting to build poly')
	print(polyName)
	print(polyVtx1)
	print(polyVtx2)
	print(polyVtx3)
	print(polyVtx4)
	cmds.polyCreateFacet( p=[(polyVtx1[0], polyVtx1[1], polyVtx1[2]), (polyVtx2[0], polyVtx2[1], polyVtx2[2]), (polyVtx3[0], polyVtx3[1], polyVtx3[2]), (polyVtx4[0], polyVtx4[1], polyVtx4[2])], name=polyName )
	cmds.parent(polyName, 'bridgePolys_grp')

def planTwoNest(nestKey, nestVal):
	sdAvtx=nestVal['sideA']
	sdBvtx=nestVal['sideB']
	polyVtx1 = sideAndNo(sdAvtx, 0)
	polyVtx2 = sideAndNo(sdAvtx, 1)
	polyVtx3 = sideAndNo(sdBvtx, 1)
	polyVtx4 = sideAndNo(sdBvtx, 0)
	buildPoly('sBdg_'+nestKey+'_p1', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

def planFiveNest(nestKey, nestVal, fstSd, lstSd):
	fstSdvtx=nestVal[fstSd]
	lstSdvtx=nestVal[lstSd]
	polyVtx1 = sideAndNo(fstSdvtx, 0)
	polyVtx2 = sideAndNo(fstSdvtx, 1)
	polyVtx3=[]
	for ltr in 'XYZ':
		polyVtx3.append(((smartBridgeDict['locs'][str(fstSdvtx[1])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[0])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[1])][ltr]))/3)
	midPt1=polyVtx3
	polyVtx4 = sideAndNo(lstSdvtx, 0)
	buildPoly('sBdg_'+nestKey+'_p1', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx3= sideAndNo(fstSdvtx, 2)
	polyVtx4= sideAndNo(fstSdvtx, 1)
	polyVtx1=midPt1
	polyVtx2=[]
	for ltr in 'XYZ':
		polyVtx2.append(((smartBridgeDict['locs'][str(fstSdvtx[2])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[1])][ltr]))/2)
	midPt2=polyVtx2
	buildPoly('sBdg_'+nestKey+'_p2', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1= midPt1
	polyVtx2= midPt2
	polyVtx3= sideAndNo(lstSdvtx, 1)
	polyVtx4= sideAndNo(lstSdvtx, 0)
	buildPoly('sBdg_'+nestKey+'_p3', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1= sideAndNo(fstSdvtx, 2)
	polyVtx2= sideAndNo(fstSdvtx, 3)
	polyVtx3=[]
	for ltr in 'XYZ':
		polyVtx3.append(((smartBridgeDict['locs'][str(fstSdvtx[3])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[1])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[2])][ltr]))/3)
	midPt3=polyVtx3
	polyVtx4= midPt2
	buildPoly('sBdg_'+nestKey+'_p4', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1= midPt2
	polyVtx2= midPt3
	polyVtx3= sideAndNo(lstSdvtx, 2)
	polyVtx4= sideAndNo(lstSdvtx, 1)
	buildPoly('sBdg_'+nestKey+'_p5', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1= sideAndNo(fstSdvtx, 3)
	polyVtx2= sideAndNo(fstSdvtx, 4)
	polyVtx3= sideAndNo(lstSdvtx, 2)
	polyVtx4= midPt3
	buildPoly('sBdg_'+nestKey+'_p6', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

def planFourNest(nestKey, nestVal, fstSd, lstSd):
	fstSdvtx=nestVal[fstSd]
	lstSdvtx=nestVal[lstSd]
	polyVtx1= sideAndNo(fstSdvtx, 0)
	polyVtx2= sideAndNo(fstSdvtx, 1)
	polyVtx3=[]
	for ltr in 'XYZ':
		polyVtx3.append(((smartBridgeDict['locs'][str(fstSdvtx[1])][ltr])+(smartBridgeDict['locs'][str(fstSdvtx[2])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[0])][ltr]))/3)
	midPt1=polyVtx3
	polyVtx4= sideAndNo(lstSdvtx, 0)
	buildPoly('sBdg_'+nestKey+'_p1', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1= sideAndNo(fstSdvtx, 1)
	polyVtx2= sideAndNo(fstSdvtx, 2)
	polyVtx3=[]
	for ltr in 'XYZ':
		polyVtx3.append(((smartBridgeDict['locs'][str(fstSdvtx[1])][ltr])+(smartBridgeDict['locs'][str(fstSdvtx[2])][ltr])+(smartBridgeDict['locs'][str(lstSdvtx[1])][ltr]))/3)
		midPt2=polyVtx3
	polyVtx4=midPt1
	buildPoly('sBdg_'+nestKey+'_p2', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1= sideAndNo(fstSdvtx, 2)
	polyVtx2= sideAndNo(fstSdvtx, 3)
	polyVtx3= sideAndNo(lstSdvtx, 1)
	polyVtx4=midPt2
	buildPoly('sBdg_'+nestKey+'_p3', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

	polyVtx1=midPt1
	polyVtx2=midPt2
	polyVtx3= sideAndNo(lstSdvtx, 1)
	polyVtx4= sideAndNo(lstSdvtx, 0)
	buildPoly('sBdg_'+nestKey+'_p4', polyVtx1, polyVtx2, polyVtx3, polyVtx4)

def sideAndNo(sideAB, i):
	polyVtx = []
	for ltr in 'XYZ':
		polyVtx.append(smartBridgeDict['locs'][str(sideAB[i])][ltr])
	return polyVtx

def checkFstLocs():
	cmds.select('sideA_1_loc', 'sideB_1_loc')

def reloadTool(sbWin, *args):
	cmds.deleteUI(sbWin, window=True)
	smartBridgeDict={}
	smartBridgeDict.clear()
	smartBridgeDict={
		'sideA':{
			'vertsNo':0
		},
		'sideB':{
			'vertsNo':0
		},
		'dmdsSwitch':{
			'2':2,
			'3':5,
			'4':2,
			'5':3
		},
		'nests':{

		},
		'main_mesh':'nomesh'
	}
	runSmartBridge()


smartBridgeDict={
	'sideA':{
		'vertsNo':0
	},
	'sideB':{
		'vertsNo':0
	},
	'dmdsSwitch':{
		'2':2,
		'3':5,
		'4':2,
		'5':3
	},
	'nests':{

	},
	'main_mesh':'nomesh'
}

def runSmartBridge():
	sbWin=cmds.window(widthHeight=(200, 200))
	cmds.columnLayout()
	cmds.text(label='SmartBridge Tool')
	cmds.rowLayout(numberOfColumns=3)
	cmds.button(label='SideA', command=partial(storeSide, 'sideA'))
	cmds.button(label='PickAsFstVtx', command=partial(pickAsFstVtx, 'sideA'))
	cmds.setParent('..')
	cmds.rowLayout(numberOfColumns=3)
	cmds.button(label='SideB', command=partial(storeSide, 'sideB'))
	cmds.button(label='PickAsFstVtx', command=partial(pickAsFstVtx, 'sideB'))
	cmds.setParent('..')
	cmds.button(label='Bridge', command=partial(startBridge, invSdBChk))
	cmds.button(label='ReloadTool', command=partial(reloadTool, sbWin))
	cmds.setParent('..')
	cmds.showWindow(sbWin)
	cmds.window(sbWin, edit=True, visible=True)

runSmartBridge()
