#!/usr/bin/env python

import os, re, sys

if len(sys.argv) < 2:
    print "usage: %s <recordfile>" % sys.argv[0]
    sys.exit(1)

# Read record
filename = sys.argv[1]
fd = file(filename)
record = fd.read()
fd.close()

# Update revision
newrecord = []
lbreak = "\r\n"
for line in record.splitlines():
    if line.startswith('# Revision:'):
        rev = int(line.split(':')[1]) + 1
        line = '# Revision: %u' % rev
    newrecord.append(line)
newrecord = lbreak.join(newrecord)

# Setup mail values
address = 'freedb-submit@freedb.org'
ident = os.path.splitext(filename)[0]
if not re.search('^[a-z]+ [a-z0-9]{8}$', ident):
    sys.exit(ident + " is not a valid freedb `discid genre' pair")
subject = "cddb %s" % ident

# Save updated record
fd = file(filename, "w")
fd.write(newrecord)
fd.close()

# Send mail
print "Subject:", subject
cmd = 'cat "%s" | mutt -s "%s" %s' % (filename, subject, address)
print "%", cmd
os.system(cmd)
