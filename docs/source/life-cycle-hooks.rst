Life Cycle Hooks
================

Hooks are functions that allow you to "hook into" the life cycle events and state of
Elements. Their usage should always follow the :ref:`**Rules of Hooks**`. For most use
cases the :ref:`**Basic Hooks**` should be enough, however the remaining
:ref:`**Supplementary Hooks**` should fulfill less common scenarios.

.. note::

    Not all of React's built-in hooks have been implemented. In the future they will be
    added, but if you have a particular need for a missing hook post an issue [GH203]_.

.. contents::
  :local:
  :depth: 1


**Basic Hooks**
---------------

Common hooks that should fulfill a majority of use cases.


use_state
---------

.. code-block::

    state, set_state = use_state(initial_state)

Returns a stateful value and a function to update it.

During the first render the ``state`` will be identical to the ``initial_state`` passed
as the first argument. However in subsiquent renders ``state`` will take on the value
passed to ``set_state``.

.. code-block::

    set_state(new_state)

The ``set_state`` function accepts a ``new_state`` as its only argument and schedules a
re-render of the element where ``use_state`` was initially called. During these
subsiquent re-renders the ``state`` returned by ``use_state`` will take on the value
of ``new_state``.

.. note::

    The identity of ``set_state`` is guaranteed to be preserved across renders. This
    means it can safely be omited from dependency lists in :ref:`use_effect` or
    :ref:`use_callback`.


Functional Updates
..................

If the new state is computed from the previous state, you can pass a function which
accepts a single argument (the previous state) and returns the next state. Consider this
simple use case of a counter where we've pulled out logic for incrementing and
decrementing the count:

.. literalinclude:: examples/use_state_counter.py

.. interactive-widget:: use_state_counter

We use the functional form for the "+" and "-" buttons since the next ``count`` depends
on the previous value, while for the "Reset" button we simple assign the
``initial_count`` since it's independent of the prior ``count``. This is a trivial
example, but it demonstrates how complex state logic can be factored out into well
defined and potentially reuseable functions.


Lazy Initial State
..................

In cases where it is costly to create the initial value for ``use_state``, you can pass
a constructor function that accepts no arguments instead - it will be called on the
first render of an element, but will be disregarded in all following renders:

.. code-block::

    state, set_state = use_state(lambda: some_expensive_computation(*args, **kwargs))


Skipping Updates
................

If you update a State Hook to the same value as the current state then the element which
owns that state will not be rendered again. We check ``if new_state is current_state``
in order to determine whether there has been a change. Thus the following would not
result in a re-render:

.. code-block::

    state, set_state = use_state([])
    set_state(state)


use_effect
----------

.. code-block::

    use_effect(did_render)

The ``use_effect`` hook accepts a function which is may be imperative, or mutate state.
The function will be called once the element has rendered, that is, when the
element's render function and those of any child elements it produces have rendered
successfully.

Mutations, subscriptsion, delayed actions, and other `side effects`_ can cause
unexpected bugs if placed in the main body of an element's render function. Thus the
``use_effect`` hook provides a way to safely escape the purely functional world of
element render functions.

.. note::

    Normally in react the ``did_render`` function is called once an update has been
    commited to the screen. Since no such action is performed by IDOM, and the time
    at which the update is displayed cannot be known we are unable to achieve parity
    with this behavior.


Cleaning Up Effects
...................

If the effect you wish to enact creates resources you'll probably need to clean them up.
In such cases you may simply return a function the addresses this from the function
which created the resource. Consider the case of opening and then closing a connection:

.. code-block::

    def establish_connection():
        connection = open_connection(url)
        return connection.close

    use_effect(establish_connection)

The clean-up function will be run before the element is unmounted or, before the next
effect is triggered when the element re-renders. You can
:ref:`conditionally fire events <Conditional Effects>` to avoid triggering them each
time an element renders.


Conditional Effects
...................

By default effects are triggered after ever successful render to ensure that all state
referenced by the effect is up to date. However you can limit the number of times an
effect is fired by specifying exactly what state the effect depends on. In doing so
the effect will only occur when the given state changes:

.. code-block::

    def establish_connection():
        connection = open_connection(url)
        return connection.close

    use_effect(establish_connection, [url])

Now a new connection will only be estalished if a new ``url`` is provided.


**Supplementary Hooks**
-----------------------

Hooks that fulfill some less common, but still important use cases using variations of
the :ref:`**Basic Hooks**`.


use_reducer
-----------

.. code-block::

    state, dispatch_action = use_reducer(reducer, initial_state)

An alternative and derivative of :ref:`use_state` the ``use_reducer`` hook, instead of
directly assigning a new state, allows you to specify an action which will transition
the previous state into the next state. This transition is defined by a reducer function
of the form ``(current_state, action) -> new_state``. The ``use_reducer`` hook then
returns the current state and a ``dispatch_action`` function that accepts an ``action``
and causes a transition to the next state via the ``reducer``.

``use_reducer`` is generally prefered to ``use_state`` if logic for transitioning from
one state to the next is especially complex or involves nested data structures.
``use_reducer`` can also be used to collect several ``use_state`` calls together - this
may be slightly more performant as well as being preferable since there is only one
``dispatch_action`` callback versus the many ``set_state`` callbacks.

We can rework the :ref:`Function Updates` counter example to use ``use_reducer``:

.. literalinclude:: examples/use_reducer_counter.py

.. interactive-widget:: use_reducer_counter

.. note::

    The identity of the ``dispatch_action`` function is guaranteed to be preserved
    across re-renders throughout the lifetime of the element. This means it can safely
    be omited from dependency lists in :ref:`use_effect` or :ref:`use_callback`.


use_callback
------------

.. code-block::

    memoized_callback = use_callback(lambda: do_something(a, b), [a, b])

A derivative of :ref:`use_memo`, the ``use_callback`` hook teturns a
`memoized <memoization>`_ callback. This is useful when passing callbacks to child
elements which check reference equality to prevent unnecessary renders. The of the
``memoized_callback`` will only change when the given depdencies do.

.. note::

    The list of "dependencies" are not passed as arguments to the function ostensibly
    though, that is what they represent. Thus any variable referenced by the function
    must be listed as dependencies. We're working on a linter to help enforce this
    [GH202]_.



use_memo
--------

.. code-block::

    memoized_value = use_memo(lambda: compute_something_expensive(a, b), [a, b])

Returns a `memoized <memoization>`_ value. By passing a constructor function accepting
no arguments and an array of dependencies for that constructor, the ``use_callback``
hook will return the value computed by the constructor. The ``memoized_value`` will only
be recomputed when a value in the array of depdencies changes. This optimizes
performance because you don't need to ``compute_something_expensive`` on every render.

If the array of depdencies is ``None`` then the constructor will be called on every
render.

Unlike ``use_effect`` the constructor function is called during each render (instead of
after) and should not incur side effects.

.. warning::

    Remember that you shouldn't optimize something else you know it's a performance
    bottleneck. Write your code without ``use_memo`` first and then add it to later
    to targeted sections that need a speed-up.

.. note::

    The list of "dependencies" are not passed as arguments to the function ostensibly
    though, that is what they represent. Thus any variable referenced by the function
    must be listed as dependencies. We're working on a linter to help enforce this
    [GH202]_.


use_ref
-------

.. code-block::

    ref_container = use_ref(initial_value)

Returns a mutable :class:`~idom.core.hooks.Ref` object that has a single
:attr:`~idom.core.hooks.Ref.current` attribute that at first contains the
``initial_state``. The identity of the ``Ref`` object will be preserved for the lifetime
of the element.

A ``Ref`` is most useful if you need to incur side effect since updating its
``.current`` attribute doesn't trigger a re-render of the element. You'll often use this
hook alongside :ref:`use_effect` or in response to element event handlers. The
:ref:`The Game Snake` provides a good use case for ``use_ref``.


**Rules of Hooks**
------------------

Under construction...

.. note::

    We're working on a linter to help enforce the rules [GH202]_.


.. links
.. =====

.. _React Hooks: https://reactjs.org/docs/hooks-reference.html
.. _side effects: https://en.wikipedia.org/wiki/Side_effect_(computer_science)
.. _memoization: https://en.wikipedia.org/wiki/Memoization
.. _premature optimization: https://en.wikiquote.org/wiki/Donald_Knuth#Computer_Programming_as_an_Art_(1974)
.. _gh issues: https://github.com/idom-team/idom/issues