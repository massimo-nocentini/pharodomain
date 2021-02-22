
import docutils

from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.domains import Domain
from sphinx.roles import XRefRole
from sphinx.util.nodes import nested_parse_with_titles, make_refnode
from sphinx.util.docutils import ReferenceRole
from sphinx import addnodes
from docutils.statemachine import StringList
import json

def doctree_resolved_handler(app):

    # D will contain the whole content, collecting from each json file.
    D = {'classes': {}, 'messages': {}}

    for filename in app.config.pharo_json_export_filenames:
        with open(filename) as fp:
            d = json.load(fp)
            D['classes'] |= d['classes']
            D['messages'] |= d['messages']

    app.builder.env.pharo_json_export = D
    print('json loaded succeessfully, with {} messages and {} classes.'.format(
        len(D['messages']), len(D['classes'])))

def nested_parse(lines, filename, directive):

    state = directive.state
    rst = StringList()

    for i, l in enumerate(lines):
        rst.append(l, filename, i)

    node = docutils.nodes.section()
    node.document = state.document

    # Parse the rst.
    nested_parse_with_titles(state, rst, node)

    return node.children


class PharoAutoClassDirective(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
            'include-comment': directives.unchanged,
            'linenos': directives.unchanged,
        }
    has_content = True

    def run(self):
        
        env = self.state.document.settings.env
        pharo_json_export = env.pharo_json_export

        className = self.arguments[0]
        classDef = pharo_json_export['classes'][className.replace('_', ' ')]
        classDef['description'] = [''] + [str(l) for l in self.content]

        # a node to reference the current class, by unpacking a unary list.
        labelnode, = nested_parse(lines=['.. _pharo-class-{}:'.format(className)],
                                  filename='labels-for-pharo-classes.rst',
                                  directive=self)

        class_comment = '\n'.join(classDef['comment'])
        include_comment = self.options.get('include-comment')

        definition = classDef['definition']

        comment_node = None
        if include_comment == 'md':
            comment_node = docutils.nodes.literal_block(text=class_comment, language='md')
        elif include_comment == 'yes':
            definition = definition + ('\n\n"{}"'.format(class_comment.replace('"', '""')))

        content_nodes = nested_parse(lines=classDef['description'],
                                     filename='{}.rst'.format(className),
                                     directive=self)

        targetid = 'pharo-class-%d' % env.new_serialno('pharo-class')
        targetnode = docutils.nodes.target('', ids=[targetid])

        definition_node = docutils.nodes.literal_block(
                text=definition,
                language='smalltalk',
                linenos=self.options.get('linenos', False))

        indexnode = addnodes.index()
        indexnode['entries'] = [
                ('single', 'Package {} contains; {}'.format(classDef['category'], className), targetid, False, None),
        ]

        env.domaindata['pharo']['classes'].append(
            ('pharo-class-{}'.format(className.lower()), className, 'pharo', env.docname, 'pharo-class-{}'.format(className.lower()), 0))

        return ([targetnode, indexnode, labelnode, definition_node] + 
                ([comment_node] if comment_node else []) + 
                content_nodes)

class PharoAutoCompiledMethodDirective(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
            'linenos': directives.unchanged,
        }
    has_content = True

    def run(self):

        env = self.state.document.settings.env
        pharo_json_export = env.pharo_json_export
                
        fullSelector = self.arguments[0]
        className, selector = fullSelector.split('>>')
        className = ' '.join(className.split('_'))

        valid_Sphinx_selector = '{}-{}'.format(className.replace(' ', '-'),     # because `Var class` could appear
                                               selector[1:].replace(':', '-'))  # because `:` delimits the label's end
                                                                                # also exclude the initial `#` symbol

        fullSelector = '{}>>{}'.format(className, selector)
        messageDef = pharo_json_export['messages'][selector[1:]]
        compiled_method = messageDef['implementors'][className]
        compiled_method['description'] = [''] + ['  ' + str(s) for s in self.content]

        # a node to reference the current message, by unpacking a unary list.
        labelnode, = nested_parse(lines=['.. _pharo-compiledMethod-{}:'.format(valid_Sphinx_selector)],   
                                  filename='labels-for-pharo-messages.rst',
                                  directive=self)

        protocol = compiled_method['category']
        sourceCode = ['"{}, protocol {}"'.format(className, protocol)] + compiled_method['sourceCode']

        content_nodes = nested_parse(lines=compiled_method['description'],
                                     filename='{}.rst'.format(fullSelector),
                                     directive=self)

        definition_node = docutils.nodes.literal_block(
                text='\n'.join(map(lambda l: l.replace('\t', ' ' * 3), sourceCode)),
                language='smalltalk',
                linenos=self.options.get('linenos', False))

        targetid = 'pharo-compiledMethod-%d' % env.new_serialno('compiledMethod')
        targetnode = docutils.nodes.target('', '', ids=[targetid])

        indexnode = addnodes.index()
        indexnode['entries'] = [
                ('single', 'Protocol {}; {}'.format(compiled_method['category'], fullSelector), targetid, False, None),
                ('single', "a {} understands; {}".format(className, selector), targetid, False, None),
        ]

        if not compiled_method['isTestMethod']:
            quintuple = ('single', '{} is understood by; {}'.format(selector, fullSelector), targetid, False, None)
            indexnode['entries'].append(quintuple)

        valid_Sphinx_selector = valid_Sphinx_selector[:-1] if valid_Sphinx_selector.endswith('-') else valid_Sphinx_selector
        env.domaindata['pharo']['compiledMethods'].append(
            ('pharo-compiledmethod-{}'.format(valid_Sphinx_selector.lower()), '{}>>{}'.format(className, selector), 'pharo', env.docname, 'pharo-compiledMethod-{}'.format(valid_Sphinx_selector).lower(), 0))

        cmNode = docutils.nodes.section()
        cmNode += targetnode
        cmNode += indexnode
        cmNode += labelnode
        cmNode += definition_node
        return cmNode.children + content_nodes

class PharoDomain(Domain):

    name = 'pharo'
    label = 'A Smalltalk domain'
    roles = {
        'cref': XRefRole(),
        'mref': XRefRole(),
    }
    directives = {
        'autoclass': PharoAutoClassDirective,
        'autocompiledmethod': PharoAutoCompiledMethodDirective,
    }
    indices = {
    }
    initial_data = {
        'classes': [],  # object list
        'compiledMethods': [],  # object list
    }

    def get_full_qualified_name(self, node):
        return '{}.{}'.format('pharo', node.arguments[0])

    def get_objects(self):
        for obj in self.data['classes']:            yield(obj)
        for obj in self.data['compiledMethods']:    yield(obj)
    
    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        
        match = [(docname, anchor)
                 for name, sig, typ, docname, anchor, prio
                 in self.get_objects() if sig == target]

        if len(match) > 0:
            todocname = match[0][0]
            targ = match[0][1]
            
            return make_refnode(builder,fromdocname,todocname, targ, contnode, targ)
        else:
            print("{} not found nothing for xref.".format(target))
            return None

def setup(app):

    app.add_config_value('pharo_json_export_filenames', [], 'html')
    app.connect('builder-inited', doctree_resolved_handler)
    app.add_domain(PharoDomain)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
