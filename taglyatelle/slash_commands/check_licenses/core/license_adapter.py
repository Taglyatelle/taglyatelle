"""Adapter pattern for check_licenses."""

from abc import ABC, abstractmethod


class LicenseAdapter(ABC):
    @abstractmethod
    def parse(self, files: list[str]) -> dict[str, str]:
        raise NotImplementedError
