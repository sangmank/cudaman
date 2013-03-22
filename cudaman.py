#!/usr/bin/env python

import subprocess, re, os, sys, libxml2, getopt
from datetime import date

global_index = {}

output_dir = "./out"
man_section_no = 3

rec_tag = re.compile(r'<a[^>]* href="#([^"]*)"[^>]*>')
rec_unfound_tag = re.compile(r'<a[^>]* href="#"[^>]*>')

def replace_tag(output):
	# for now, let's remove all the "a" tags 
	return rec_tag.sub("", output)
	#tags = [m.group(1) for m in rec_tag.finditer(output)]
	#for tag in tags:
		# if tag in global_index:
		# 	#print "Found: %s => %s"%(str(tag), str(global_index[tag]))
		# 	output = output.replace(tag, global_index[tag])
		# else:
	#	output = output.replace(tag, "")
			
	# remove missing targets
	#output = rec_unfound_tag.sub("", output)
	#return output

def handle_ref_node(entry_node, section_title):
	print "handle_ref_node: NOT IMPLEMENTED"

def get_title_and_filename_define(dt):
	title = dt.content.strip()
	return title, title.split()[1]

def index_define(entry_node, section_title):
	dts = entry_node.xpathEval('./dt')
	
	for dt in dts:
		title, filename = get_title_and_filename_define(dt)
		tags = dt.xpathEval('./a[@name]')
		for tag in tags:
			#print tag.prop("name").strip(), filename
			global_index[tag.prop("name").strip()] = filename

def proc_define(entry_node, section_title):
	pass

def index_enum(entry_node, section_title):
	pass

def proc_enum(entry_node, section_title):
	pass

rec_func = re.compile("\s+(\S+)\s*[(]")

def func_name(func_decl):
	m = rec_func.search(func_decl)
	assert m, "func name not found %s"%func_decl
	return m.group(1)

rec_tmpl = re.compile(r'^\s+template')
rec_tmpl_func = re.compile(r'template < [^>]* > *\S+\s+(\S+)')
rec_title_sanitize = re.compile(r'\s\s+', re.UNICODE)

def get_title_and_filename_func(dt):
	title = dt.content.strip()

	# removing any multiple spaces
	title = rec_title_sanitize.sub(' ', title)
	
	if rec_tmpl.match(dt.content):
		filename = rec_tmpl_func.search(title).group(1)
	elif "__device__" in title:
		filename = func_name(title[len("__device__ "):])
	else:
		filename = func_name(title)
		
	return title, filename

def index_func(entry_node, section_title):
	dts = entry_node.xpathEval('./dt')
	
	for dt in dts:
		title, filename = get_title_and_filename_func(dt)
		tags = dt.xpathEval('./a[@name]')
		for tag in tags:
			#print tag.prop("name").strip(), filename
			global_index[tag.prop("name").strip()] = filename

def proc_func(entry_node, section_title):
	dts = entry_node.xpathEval('./dt')
	
	for dt in dts:
		title, filename = get_title_and_filename_func(dt)

		if not filename:
			print "ERROR: Empty filename. Title: %s"%title
		
		assert dt.next.next.name == "dd", "dd node needs to follow dt node"

		if not re.match("^[a-zA-Z_]+.*$", filename):
			print "ERROR: weird filename. (%s) %s"%(filename, dt.content)
			return
		
		print "Writing %s"%filename
		with open("%s/%s.html"%(output_dir,filename), "w") as f:
			f.write("<h1>NAME</h1>\n%s\n\n" % filename)
			f.write("<h1>SYNOPSIS</h1>\n%s\n" % title)
			f.write("<h1>DESCRIPTION</h1>\n")
			f.write(replace_tag(dt.next.next.serialize()))
			
		template_file = "./template.man"
		
		variables = {"man_title":filename,
					 "man_sec":str(man_section_no),
					 "date":date.today().strftime("%d/%m/%y"),
					 "man_lfooter":"NVIDIA CUDA",
					 "man_cheader":section_title,
					 }
		cmd_var = " ".join(["-V '%s:%s'"%(k,v) for k,v in variables.iteritems()])

		os.system("pandoc -t man -f html %s/%s.html -o %s/%s.%d --template=%s %s"%
				  (output_dir, filename, output_dir, filename,
				   man_section_no, template_file, cmd_var))
		
def index_typedef(entry_node, section_title):
	pass

def proc_typedef(entry_node, section_title):
	pass

title_map = {
	"Defines": (index_define, proc_define),
	"Enumerations": (index_enum, proc_enum),
	"Functions": (index_func, proc_func),
	"Typedefs": (index_typedef, proc_typedef)
	}

def handle_man_node(node, node_title):
	res = node.xpathEval('./div[@class="description"]/h4[@class="sectiontitle"]')
	
	# first indexing (gather <a name>)
	for node in res:
		# node.next.next == dl node (sibling of h4)
		title_map[node.content][0](node.next.next, node_title)

	for node in res:
		# node.next.next == dl node (sibling of h4)
		title_map[node.content][1](node.next.next, node_title)
		# dl_node = node.next.next
		# assert dl_node.name == "dl", "<dl> tag is expected"
		
		
		# sys.exit(1)

def handle_annotate_node(node, node_title):
	print "handle_annotate_node: NOT IMPLEMENTED"


re_parameters = re.compile(r'<h6 class="parameter_header">\s+Parameters\s+</h6>')
re_returns = re.compile(r'<h6 class="return_header">\s+Returns\s+</h6>')
def preprocess_block(blk):
	# removing zero-width spaces (U+200B)
	blk = blk.replace(chr(0xe2) + chr(0x80) + chr(0x8b), '')

	# turning headers into h1 (to create .TH in man files for these headers)
	blk = blk.replace('<p class="p apiDesc_subtitle"><strong class="ph b">See also:</strong></p>',
					  '<h1>See Also</h1>')

	blk = re_parameters.sub('<h1>Parameters</h1>', blk)
	blk = re_returns.sub('<h1>Returns</h1>', blk)
	
	return blk
		
def process_block(blk, name_root, ext):
	# process blocks accordingly

	# Typical block structure
	#
	# Either
	# <div class="body refbody"> 
	#    (<div class="section"> ... </div>)+
	# </div>
	# or
	# <div class="topic reference apiRef apiPackage cppModule" id="group__CUDART__STREAM"><a name="group__CUDART__STREAM" shape="rect">
	#   <h4 class="fake_sectiontitle member_header"> Typedefs </h4>
	#   <dl class="members"> ...... </dl> 
	#   <h4 class="fake_sectiontitle member_header">Functions</h4>
	#   <dl class="members"> ...... </dl>
	#   <div class="description">
	#     <h4 class="sectiontitle">Typedefs</h4>
	#     <dl class="description"> ... many typedefs ... <d/>
	#   </div>
	#   <div class="description">
	#     <h4 class="sectiontitle">Functions</h4>
	#     <dl class="description"> ... many functions .. <dl/>
	#   </div>
	# </div>

	# description of each entry (in <dl class="description">
	# <dt class="description"></dt> 
	# <dd class="description"><div class="section"> .. </div></dd>
	#
	print "div %s"%(blk[blk.find("id="):blk.find("\"", blk.find("id=")+4)+1])
	
	blk = preprocess_block(blk)
	
	doc = libxml2.parseMemory(blk, len(blk))
	ctxt = doc.xpathNewContext()
	res = ctxt.xpathEval('/div/div')
	#print "Number of xpath children: %d"%len(res)
	for node in res:
		node_title = ""
		if node.xpathEval('./h3'):
			node_title = node.xpathEval('./h3')[0].content
			
		print "Node title: %s"%node_title
		
		map_handler = {"body refbody":handle_ref_node,
					   "topic reference apiRef apiPackage cppModule": handle_man_node,
					   "topic reference apiRef apiClassifier cppClassifier cppStruct cppGlobalStruct": handle_annotate_node}

		ctxt_class = node.prop("class")
		if ctxt_class in map_handler:
			map_handler[ctxt_class](node, node_title)
		else:
			print "ERROR: Inappropriate class for ctxt (%s)" % ctxt_class
	
	# TODO: post processing?

def create_api_man(html_file):
	name_root, name_ext = os.path.splitext(html_file)
	
	with open(html_file) as f:
		content = f.read()

	# stripping out the url-based references and change them to local-page references
	content = re.sub(r'<a([^>]*) href="http://docs.nvidia.com/cuda/[a-z-]+/index.html#', r'<a\1 href="#', content)
	content = re.sub(r'<a([^>]*) href="index.html#', r'<a\1 href="#', content)
	
	# removing unnecessary <div> before struct names
	content = re.sub(r'(struct&nbsp;</span><span class="member_name">\n *)<div>(<a[^>]+>[^<]+</a>)</div>', r'\1\2', content, flags=re.MULTILINE)

	content = re.sub(r'&nbsp;', r' ', content)
	content = re.sub(r'</br>', r'', content)
	content = re.sub(r'<br[^>]*>', r'<br />', content)

	# separate contents with nested0 div => blocks
	block_info = []
	blocks = []
	
	for m in re.finditer(r'<div class="[^"]*nested0[^>]*id="([^"]+)"', content):
		block_info.append((m.start(), m.group(1),))

	prev_blk_added = False
	prev_index = -1
	
	for index, blk_id in block_info:
		if prev_blk_added:
			blocks.append((content[prev_index:index]))
			prev_blk_added = False
			
		if blk_id in ("modules", "functions", "annotated", "r_main"):
			prev_blk_added = True
			prev_index = index

	if prev_blk_added:
		blocks.append(content[prev_index:])

	assert blocks, "blocks should not be empty"

	# now we have blocks.
	# let's process blocks
	post_blks = map(lambda x: process_block(x, name_root, name_ext), blocks)

def usage():
	print """Usage:

%s {options} [input_html]

Options:

  -s [sec],--section=[sec]     section number of man pages
  -o [dir],--outdir=[sec]      output directory for man pages
""" % sys.argv[0]
	
def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ho:s:", ["help", "outdir=", "section="])
	except getopt.GetoptError as err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

	for o, a in opts:
		if o == "-v":
			verbose = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-o", "--outdir"):
			output_dir = a
		elif o in ("-s", "--section"):
			man_section_no = int(a)
		else:
			print "unhandled option"
			sys.exit(1)
			
	if len(args) != 1:
		usage()
		sys.exit(1)
		
	input_html = args[0]
	
	create_api_man(input_html)
	
if __name__ == "__main__":
	main()
