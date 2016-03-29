# This file is part of Sloth.
#
# Sloth is free software: you can redistribute it and/or modify
# it under the terms of the Affero GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sloth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# Affero GNU General Public License for more details.
#
# You should have received a copy of the Affero GNU General Public License
# along with Sloth.  If not, see <http://www.gnu.org/licenses/>.
from sloth.userinput import ConversionFailed


def PresentConversionFailed(message):
    try:
        raise ConversionFailed(message)
    except ConversionFailed as e:
        print(e.failure_message)


def main(choose_, settings):
    message = 'This still needs worked on..'
    PresentConversionFailed(message)
