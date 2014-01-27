SETUP = python setup.py --quiet

all pregithub:
	$(SETUP) build

install:
	$(SETUP) install

tags:
	find -name '*.py' | egrep -v '^./build|~$$' | etags -

ifneq "$(wildcard ~/etc/mes-sites/site.mk)" ""

site: site-all

package_name = Cabot
margin_color = "\#cccccc"
caption_color = "\#f1e4eb"

LOGOURL = "/logo.png"

include ~/etc/mes-sites/site.mk

endif
