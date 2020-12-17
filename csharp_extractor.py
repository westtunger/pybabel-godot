from babel.messages.jslexer import tokenize, unquote_string


class ActiveCall:
    def __init__(self, name):
        self.name = name
        self.current_value = None
        self.value_start_line = 0

    def valid(self):
        return self.name and self.current_value

class CSharpExtractor(object):
    def __init__(self, data):
        self.data = data

        self.current_name = None
        self.active_calls = []

        self.parenthesis_level = 0

        self.results = []

    def start_call(self):
        self.active_calls.append(ActiveCall(self.current_name))
        self.current_name = None

    def end_call(self):
        call = self.active_calls.pop()

        if call.valid():
            self.add_result(call)

    def add_result(self, call):
        result = dict(
            line_number=call.value_start_line,
            content=call.current_value,
            function_name=call.name
        )
        self.results.append(result)

    def get_lines_data(self, encoding):
        """
        Returns string:line_numbers list
        Since all strings are unique it is OK to get line numbers this way.
        :rtype: list
        """
        trigger_call_prime = False

        for token in tokenize(self.data.decode(encoding), jsx=False):
            call_primed = trigger_call_prime
            trigger_call_prime = False

            if token.type == 'operator':
                if token.value == '(':
                    if call_primed:
                        self.start_call()
                    else:
                        self.parenthesis_level += 1
                elif token.value == ')':
                    if self.parenthesis_level == 0:
                        self.end_call()
                    else:
                        self.parenthesis_level -= 1
            elif token.type == 'name':
                trigger_call_prime = True
                self.current_name = token.value
            elif token.type == 'string' and len(self.active_calls) > 0:
                string_value = unquote_string(token.value)

                call = self.active_calls[-1]

                if call.current_value is None:
                    call.current_value = string_value
                    call.value_start_line = token.lineno
                else:
                    call.current_value += string_value

        return self.results


def extract_csharp(file_obj, keywords, comment_tags, options):
    """
    Custom C# extract to fix line numbers for Windows
    """
    data = file_obj.read()
    extractor = CSharpExtractor(data)

    for item in extractor.get_lines_data(options.get('encoding', 'utf-8')):
        function = item['function_name']

        if function not in keywords:
            continue

        messages = [item['content']]
        yield item['line_number'], function, tuple(messages), []
