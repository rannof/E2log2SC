#!/usr/bin/env python
# by Ran Novitsky Nof (ran.nof@gmail.com), 2015 @ BSL

# convert E2 log files to SeisComP3 xml.
# Seiscomp3 xml can be fed to Seicomp3 database using scdb.
# Examples:
#   E2log2SC.py -i events_20150214.log -o SCXML
#   scdb -i SCXML -d mysql://sysop:sysop@localhost/seiscomp3
# or:
#   cat [ELARMSXMLFILE] | E2log2SC.py | scdb -i - -d mysql://sysop:sysop@localhost/seiscomp3
# or:
#   E2log2SC.py -i events_*.log | scdb -i - -d mysql://sysop:sysop@localhost/seiscomp3
#
#
#
# ***********************************************************************************
# *    Copyright (C) by Ran Novitsky Nof                                            *
# *                                                                                 *
# *    E2log2SC.py is free software: you can redistribute it and/or modify          *
# *    it under the terms of the GNU Lesser General Public License as published by  *
# *    the Free Software Foundation, either version 3 of the License, or            *
# *    (at your option) any later version.                                          *
# *                                                                                 *
# *    This program is distributed in the hope that it will be useful,              *
# *    but WITHOUT ANY WARRANTY; without even the implied warranty of               *
# *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                *
# *    GNU Lesser General Public License for more details.                          *
# *                                                                                 *
# *    You should have received a copy of the GNU Lesser General Public License     *
# *    along with this program.  If not, see <http://www.gnu.org/licenses/>.        *
# ***********************************************************************************


import argparse,sys,os,re
import seiscomp3.IO as scio
import seiscomp3.DataModel as scdatamodel
import seiscomp3.Core as sccore

# command line parser
def is_valid_outfile(parser, arg):
    if arg=='-':
      return '-'
    if os.path.exists(arg):
      parser.error("The file %s exist!" % arg)
    else:
      try:
        f = open(arg, 'w')
        f.close()
      except Exception,msg:
        parser.error(msg)
      return arg  # return an open file handle

parser = argparse.ArgumentParser(
         formatter_class=argparse.RawDescriptionHelpFormatter,
         description='''E2lgo2SC - ElarmS E2 log to SeisComP3 event xml converter''',
         epilog='''Created by Ran Novitsky Nof (ran.nof@gmail.com), 2015 @ BSL''')
parser.add_argument('-o',metavar='OutXML',default='-',help='Output xml file (Seiscomp3)',type=lambda x:is_valid_outfile(parser, x) )
parser.add_argument('-i',metavar='InXML',nargs='+',default='-',help='input E2 log file(s) (ElarmS).',type=argparse.FileType('r'))

#variables
AGENCYID='GII'
AUTHOR='E2'

def km2deg(km):
  return km/111.13291490135191

class E2LogParser(object):
  def __init__(self,xmlOut):
    self.ar = scio.XMLArchive() # seiscomp xml creator
    self.ar.setFormattedOutput(True) # output formatted xml file
    self.xmlOut = xmlOut
    self.eparams = scdatamodel.EventParameters()
    self.eparams.SetIdGeneration(True)
    self.eparams.SetIdPattern('@classname@#@time/%Y%m%d%H%M%S.%f@.@id@')
    self._stage=2
    self.Eid='0'

  def write(self,obj=None,output_file=None):
    if not output_file: output_file=self.xmlOut
    if not obj: obj = self.eparams
    self.ar.create(output_file)
    self.ar.writeObject(obj)
    self.ar.close()

  def getCreationTime(self,timeStamp):
    creationTime= sccore.Time.GMT()
    creationTime.fromString(creationTime.iso().split('T')[0]+timeStamp,"%F%T.%f")
    return creationTime

  def parseFiles(self,filelist):
    for f in filelist:
      for line in f.readlines():
  #      try:
        if re.search('.*E:I:[TF ][: ] ',line): self.parseLogLine(line)
  #      except Exception as E:
  #        print line
  #        sys.exit(str(E))
      f.close()
    self.write()

  def parseLogLine(self,line):
    'convert log lines to sc3 objects'
    if 'E:I: ' in line or 'E:I:F' in line: # origin parameters
      #E:I:H: eventid ver evlat evlon dep mag time latu lonu depu magu timeu lk nTb nSb nT nS ave rms fitok splitok near statrig active inact nsta percnt prcntok mindist maxdist distok azspan Mok nSok Lok Tdif Tok Aok Ast alert_time
      timeStamp,Eid,ver,lat,lon,depth,mag,otTxt,latu,lonu,depu,magu,timeu,lk,nTb,nSb,nT,nS,ave,rms,fitok,splitok,near,statrig,active,inact,nsta,percnt,prcntok,mindist,maxdist,distok,azspan,Mok,nSok,Lok,Tdif,Tok,Aok,Ast,atimeTxt = line.strip().split() # parse line
      creationTime = sccore.Time() # creation time placeholder
      creationTime.fromString(atimeTxt,'%Y-%m-%dT%H:%M:%S.%f') # get creation time
      ot = sccore.Time() # origin time placeholder
      ot.fromString(otTxt,'%Y-%m-%dT%H:%M:%S.%f') # get origin time
      self._origin = self.createOrigin(ot=ot,otu=timeu,lat=lat,lon=lon,depth=depth,mag=mag,latu=latu,lonu=lonu,depthu=depu,magu=magu,reported=Aok,creationTime=creationTime) # add origin
      self.addOriginQuality(self._origin,nT, nS,azspan,maxdist,mindist,rms) # add origin quality
      self.eparams.add(self._origin)
      if int(Eid) > 0:# if event has a positive id number
        self.addEvent(Eid,origins=[self._origin]) #add origin to event
    if 'E:I:T: ' in line: # Trigger
      #E:I:T:H: eventid ver update order sta chan net loc lat lon trigger_time log_taup taup_snr log_pd pd_snr log_pv pv_snr pa pa_snr assoc tpmag utpm pdmag updm uch ukm upd ups utp uts distkm azimuth [tterr plen sps toffset arrtime protime fndtime quetime sndtime e2time buftime alert]
      timeStamp,Eid,ver,update,order,sta,chn,net,loc,lat,lon,trigger_time,log_taup,taup_snr,log_pd,pd_snr,log_pv,pv_snr,pa,pa_snr,assoc,tpmag,utpm,pdmag,updm,uch,ukm,upd,ups,utp,uts,distkm,azimuth = line.strip().split()[:33]# parse line
      pTime = sccore.Time()
      pTime.fromString(trigger_time,'%Y-%m-%dT%H:%M:%S.%f') # get pick time
      if loc=='--': loc = '' # adjust location format
      creationTime = sccore.Time()
      creationTime.fromString(trigger_time.split('T')[0]+'T'+timeStamp.split("|")[0],'%Y-%m-%dT%H:%M:%S.%f') # get creation time
      pick = self.addPick(pTime,net,sta,loc,chn,azimuth,distkm,latency=0,creationTime=creationTime) # add pick
      self.addArrival(self._origin,pick.publicID(),azimuth,distkm) # add arrival to current origin

  def addCreationInfo(self,parent=None,creationTime=None,agencyID=AGENCYID,author=AUTHOR,modificationTime=None):
    if not creationTime: creationTime = sccore.Time.GMT()
    if not modificationTime: modificationTime = sccore.Time.GMT()
    ci = scdatamodel.CreationInfo()
    ci.setAgencyID(agencyID)
    ci.setCreationTime(creationTime)
    ci.setAuthor(author)
    ci.setModificationTime(modificationTime)
    if parent: parent.setCreationInfo(ci)
    return ci

  def createOrigin(self,ot,lat,lon,depth=8,otu=0,latu=0,lonu=0,depthu=0,mag=-99,magu=0,reported=0,creationTime=None,agencyID=AGENCYID,author=AUTHOR):
    if not creationTime: creationTime=sccore.Time.GMT()
    lat,lon,depth,otu,latu,lonu,depthu = [float(i) for i in lat,lon,depth,otu,latu,lonu,depthu] # convert values to floats
    origin = scdatamodel.Origin('')
    self.eparams.GenerateId(origin)
    origin.setLongitude(scdatamodel.RealQuantity(lon))
    origin.longitude().setUncertainty(lonu)
    origin.setLatitude(scdatamodel.RealQuantity(lat))
    origin.latitude().setUncertainty(latu)
    origin.setDepth(scdatamodel.RealQuantity(depth))
    origin.depth().setUncertainty(depthu)
    origin.setTime(scdatamodel.TimeQuantity(ot))
    origin.time().setUncertainty(otu)
    origin.setEvaluationMode(1)
    if int(reported): origin.setEvaluationStatus(scdatamodel.REPORTED)
    self.addCreationInfo(origin,creationTime=creationTime,agencyID=AGENCYID,author=AUTHOR)
    self.addMagnitude(origin,magval=mag,magu=magu,creationTime=creationTime)
    return origin

  def updateOrigin(self,origin,PID=None,ot=None,lat=None,lon=None,depth=None,mag=None,otu=None,latu=None,magu=None,lonu=None,depthu=None,creationTime=None,modificationTime=None):
    if PID:
      origin.setPublicID(PID)
    if ot:
      origin.setTime(scdatamodel.TimeQuantity(ot))
    if lat:
      origin.setLatitude(scdatamodel.RealQuantity(float(lat)))
    if lon:
      origin.setLongitude(scdatamodel.RealQuantity(float(lon)))
    if depth:
      origin.setDepth(scdatamodel.RealQuantity(float(depth)))
    if latu:
      origin.latitude().setUncertainty(float(latu))
    if lonu:
      origin.longitude().setUncertainty(float(lonu))
    if depthu:
      origin.depth().setUncertainty(float(depthu))
    if otu:
      origin.time().setUncertainty(float(otu))
    if creationTime:
      ci = origin.creationInfo()
      ci.setCreationTime(creationTime)
    if modificationTime:
      ci = origin.creationInfo()
      ci.setModificationTime(creationTime)
    if mag or magu:
      m = origin.magnitude(0)
      if mag: m.setMagnitude(scdatamodel.RealQuantity(mag))
      if magu: m.magnitude ().setUncertainty(magu)
      if modificationTime:
        ci = m.creationInfo()
        ci.setModificationTime(creationTime)

  def addMagnitude(self,parent,magval,magu=0,creationTime=None,agencyID=AGENCYID,author=AUTHOR):
    magval=float(magval)
    magu=float(magu)
    if not creationTime: creationTime=sccore.Time.GMT()
    mag = scdatamodel.Magnitude('')
    self.eparams.GenerateId(mag,parent.publicID()+'#netMag.M')
    mag.setMagnitude(scdatamodel.RealQuantity(magval))
    mag.magnitude().setUncertainty(magu)
    self.addCreationInfo(mag, creationTime, agencyID, author)
    mag.setType('M')
    parent.add(mag)

  def copyMag(self,originPID):
    if self._origin.magnitudeCount():
      mag = scdatamodel.Magnitude.Cast(self._origin.magnitude(0).clone())
      mag.setPublicID(originPID+'#netMag.M')
    return mag

  def copyArrivals(self):
    arrivals = []
    for i in xrange(self._origin.arrivalCount()):
      arrivals += [scdatamodel.Arrival.Cast(self._origin.arrival(i).clone())]
    return arrivals

  def copyOrigin(self,creationTime=None,agencyID=AGENCYID,author=AUTHOR,magoff=True,modificationTime=None):
    if not creationTime: creationTime=sccore.Time.GMT()
    origin = scdatamodel.Origin.Cast(self._origin.clone())
    self.eparams.GenerateId(origin)
    #update arrivals
    arrivals = self.copyArrivals()
    for a in arrivals:
      origin.add(a)
    self.updateOrigin(origin,creationTime=creationTime,modificationTime=modificationTime)
    if not magoff and self._origin.magnitudeCount():
      mag = self.copyMag(origin.publicID())
      origin.add(mag)
    self.eparams.add(origin)
    self._origin = origin
    return origin

  def addOriginQuality(self,origin, ntrig, nsta,azspan,maxdist,mindist,staerr): # add origin quality
    ntrig, nsta = [int(i) for i in (ntrig, nsta)]
    azgap = 360-float(azspan)
    maxdist = km2deg(float(maxdist))
    mindist = km2deg(float(mindist))
    staerr = float(staerr)
    oq = scdatamodel.OriginQuality()
    oq.setUsedPhaseCount(ntrig)
    oq.setAssociatedPhaseCount(ntrig)
    oq.setUsedStationCount(nsta)
    oq.setAssociatedStationCount(nsta)
    oq.setAzimuthalGap(azgap)
    oq.setMaximumDistance(maxdist)
    oq.setMinimumDistance(mindist)
    oq.setStandardError(staerr)
    origin.setQuality(oq)
    return oq

  def addEvent(self,Eid,origins=[],creationTime=None,agencyID=AGENCYID,author=AUTHOR):
    if not creationTime: creationTime=sccore.Time.GMT()
    new = False
    event = self.eparams.findEvent(Eid)
    if not event:
      event=scdatamodel.Event(Eid)
      self.addCreationInfo(event, creationTime, agencyID, author)
      self.eparams.add(event)
      new = True
    event.creationInfo().setModificationTime(creationTime)
    for origin in origins:
      event.add(scdatamodel.OriginReference(origin.publicID()))
      if new: event.setPreferredOriginID(origin.publicID())
      if origin.magnitudeCount():
        magid = origin.magnitude(origin.magnitudeCount()-1).publicID()
        event.setPreferredMagnitudeID(magid)
        event.setPreferredOriginID(origin.publicID())
    if not int(Eid)<0: self.eparams.add(event)

  def addPick(self,pTime,net,sta,loc,chn,azimuth=0,distkm=0,latency=0,creationTime=None,agencyID=AGENCYID,author=AUTHOR):
    if not creationTime: creationTime=sccore.Time.GMT()
    PID = "%s-%s.%s.%s.%s"%(pTime.toString("%Y%m%d.%H%M%S.%f"),net,sta,loc,chn)
    pick = self.eparams.findPick(PID)
    if pick: return pick
    pick = scdatamodel.Pick(PID)
    pick.setTime(scdatamodel.TimeQuantity(pTime))
    Wid = scdatamodel.WaveformStreamID()
    Wid.setNetworkCode(net)
    Wid.setStationCode(sta)
    Wid.setLocationCode(loc)
    Wid.setChannelCode(chn)
    pick.setWaveformID(Wid)
    pick.setMethodID('ElarmS')
    phase = scdatamodel.Phase('P')
    pick.setPhaseHint(phase)
    pick.setEvaluationMode(1)
    self.addCreationInfo(pick,creationTime,agencyID,author)
    self.eparams.add(pick)
    return pick

  def addArrival(self,parent,pickID,azimuth,distance):
    arrival = scdatamodel.Arrival()
    arrival.setPickID(pickID)
    phase = scdatamodel.Phase('P')
    arrival.setPhase(phase)
    arrival.setWeight(1.0)
    arrival.setAzimuth(float(azimuth))
    arrival.setTimeUsed(True)
    arrival.setPreliminary(True)
    arrival.setTimeResidual(0.001)
    arrival.setDistance(km2deg(float(distance)))
    parent.add(arrival)
    return arrival


if __name__=='__main__':
  # parse the arguments
  args = parser.parse_args(sys.argv[1:])
  E2 = E2LogParser(args.o)
  if not type(args.i) is list: args.i = [args.i]
  E2.parseFiles(args.i)
