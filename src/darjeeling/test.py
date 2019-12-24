# -*- coding: utf-8 -*-
from typing import (Sequence, Iterator, TypeVar, Dict, Any, Sequence, Generic,
                    Type, ClassVar, Optional, NoReturn, Callable, Tuple,
                    Mapping)
import abc
import inspect

import attr
import bugzoo

from .core import TestOutcome, Test
from .config import TestSuiteConfig
from .container import ProgramContainer
from .environment import Environment

T = TypeVar('T', bound=Test)
C = TypeVar('C', bound=TestSuiteConfig)

_NAME_TO_TEST_SUITE: Dict[str, Type['TestSuite']] = {}
_CONFIG_TO_TEST_SUITE: Dict[Type['TestSuiteConfig'], Type['TestSuite']] = {}


def register(name: str) -> Callable[[Type['TestSuite']], Type['TestSuite']]:
    """Registers a test suite under a given name."""
    def register_hook(class_: Type['TestSuite']) -> Type['TestSuite']:
        def err(message: str) -> NoReturn:
            m = f"Failed to register test suite [{class_.__name__}]: {message}"
            raise TypeError(m)

        if name in _NAME_TO_TEST_SUITE:
            err(f'name already in use [{name}]')
        if not issubclass(class_, TestSuite):
            err('class is not a subclass of TestSuite')
        if inspect.isabstract(class_):
            err('cannot register abstract class')
        if not hasattr(class_, 'Config'):
            err('class does not have nested Config class')
        if not issubclass(class_.Config, TestSuiteConfig):
             err('nested Config class must not be abstract')
        if class_.Config in _CONFIG_TO_TEST_SUITE:
            err('nested Config class already in use by another test suite class')  # noqa

        _NAME_TO_TEST_SUITE[name] = class_
        _CONFIG_TO_TEST_SUITE[class_.Config] = class_
        return class_

    return register_hook


class TestSuite(Generic[T]):
    Config: ClassVar[Type[TestSuiteConfig]]

    @classmethod
    @abc.abstractmethod
    def from_config(cls,
                    cfg: TestSuiteConfig,
                    environment: Environment,
                    bug: bugzoo.Bug
                    ) -> 'TestSuite':
        test_suite_class = _CONFIG_TO_TEST_SUITE[cfg.__class__]
        return test_suite_class.from_config(cfg, environment, bug)

    @abc.abstractmethod
    def __len__(self) -> int:
        ...

    @abc.abstractmethod
    def __iter__(self) -> Iterator[Test]:
        ...

    @abc.abstractmethod
    def __getitem__(self, name: str) -> Test:
        ...

    @abc.abstractmethod
    def execute(self,
                container: ProgramContainer,
                test: T,
                *,
                coverage: bool = False
                ) -> TestOutcome:
        """Executes a given test inside a container.

        Parameters
        ----------
        container: ProgramContainer
            The container in which the test should be executed.
        test: T
            The test that should be executed.
        coverage: bool
            If :code:`True`, the test harness will be instructed to run the
            test in coverage collection mode. If no such mode is supported,
            the test will be run as usual.

        Returns
        -------
        TestOutcome
            A concise summary of the test execution.
        """
        ...



@attr.s(frozen=True, slots=True, auto_attribs=True)
class BugZooTest(Test):
    _test: bugzoo.core.TestCase

    @property
    def name(self) -> str:
        return self._test.name


@register('bugzoo')
@attr.s(frozen=True, auto_attribs=True, slots=True)
class BugZooTestSuite(TestSuite[BugZooTest]):
    _environment: Environment
    _tests: Tuple[BugZooTest, ...]
    _name_to_test: Mapping[str, BugZooTest] = attr.ib(repr=False)

    @attr.s(frozen=True)
    class Config(TestSuiteConfig):
        @classmethod
        def from_dict(cls,
                      d: Dict[str, Any],
                      dir_: Optional[str] = None
                      ) -> TestSuiteConfig:
            return cls()

    @classmethod
    def from_config(cls,
                    cfg: TestSuiteConfig,
                    environment: Environment,
                    bug: bugzoo.Bug
                    ) -> 'TestSuite':
        tests = tuple(BugZooTest(t) for t in bug.tests)
        name_to_test = {t.name: t for t in tests}
        return BugZooTestSuite(environment, tests, name_to_test)

    def __len__(self) -> int:
        return len(self._name_to_test)

    def __iter__(self) -> Iterator[Test]:
        yield from self._tests

    def __getitem__(self, name: str) -> Test:
        return self._name_to_test[name]

    def execute(self,
                container: ProgramContainer,
                test: BugZooTest,
                *,
                coverage: bool = False
                ) -> TestOutcome:
        bz = self._environment.bugzoo
        bz_outcome = bz.containers.test(container._bugzoo, test._test)
        return TestOutcome(bz_outcome.passed, bz_outcome.duration)
