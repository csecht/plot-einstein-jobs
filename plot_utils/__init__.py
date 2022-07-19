from . import platform_check, vcheck

__author__ = 'Craig S. Echt'
__version__ = '0.0.9'
__copyright__ = 'Copyright (c) 2022 C.S. Echt, under GNU General Public License'

LICENSE = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.
"""

# Program will exit if any check fails.
platform_check.check_platform()
vcheck.minversion('3.7')


